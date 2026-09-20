# Spell Checker & Autocomplete

A small, fully working, pure-stdlib Python project that implements:

- a **Trie** (prefix tree) for fast prefix-based **autocomplete**, ranked by word frequency
- **Levenshtein edit distance**, implemented from scratch with dynamic programming
- a **BK-tree** built over that Levenshtein metric, so spell-check suggestion search doesn't have to brute-force every dictionary word

No third-party dependencies. Everything — the trie, the DP edit-distance
algorithm, and the BK-tree pruning — is implemented from scratch.

## Quick start

```bash
python speller.py check helo
python speller.py autocomplete cat
```

Example output:

```text
$ python speller.py check helo
"helo" is NOT a known word. Did you mean:
  1. hell  (edit distance 1, frequency 1)
  2. he  (edit distance 2, frequency 3850)
  3. her  (edit distance 2, frequency 3785)
  4. well  (edit distance 2, frequency 3485)
  5. tell  (edit distance 2, frequency 3310)

$ python speller.py autocomplete cat
Completions for "cat":
  1. cat  (frequency 2225)
  2. catalepsy  (frequency 1)
  3. cataphylla  (frequency 1)
  4. catchingly  (frequency 1)
  5. catepuce  (frequency 1)
```

("hello" isn't in the bundled demo word list, which is why "hell" — an
edit distance of 1 away — wins over it. See [Word list](#word-list) below.)

Run the tests:

```bash
python -m unittest discover -s tests -v
```

## Project layout

```
speller.py       CLI entry point + Speller class tying everything together
trie.py          Trie data structure (insert, exact lookup, prefix search, autocomplete)
levenshtein.py   Levenshtein edit distance, from-scratch dynamic programming
bktree.py        BK-tree: approximate nearest-neighbor search over edit distance
data/wordlist.txt  Curated demo dictionary: "<word> <frequency>" per line
tests/           35 unit tests (unittest, stdlib only)
```

## The Trie

`trie.py` implements a standard prefix tree: each node maps a character to
a child node, and a node marks `is_word=True` plus a `frequency` count when
a word ends there.

- `insert(word, frequency)` lowercases the word and walks/creates a path of
  nodes, one per character. Inserting the same word twice **adds** to its
  existing frequency rather than overwriting it.
- `contains(word)` walks the same path and checks `is_word` on the final
  node — this is exact-word lookup, O(len(word)).
- `words_with_prefix(prefix)` walks to the node for `prefix`, then does a
  DFS over its subtree collecting every complete word found — this is the
  basis of autocomplete. An empty prefix walks from the root, i.e. "list
  everything" rather than an error.
- `autocomplete(prefix, limit)` calls `words_with_prefix` and sorts the
  results by `(-frequency, word)` — most frequent first, alphabetical as a
  tiebreaker — then truncates to `limit`.

Storing frequency at terminal nodes (rather than just a set of strings) is
what lets autocomplete rank "the" ahead of "theodolite" even though a plain
trie would return them in no particular order.

## Levenshtein edit distance (from scratch)

`levenshtein.py` computes the classic **Wagner–Fischer** dynamic-programming
edit distance: the minimum number of single-character insertions,
deletions, and substitutions needed to turn string `a` into string `b`.

```
dp[i][j] = edit distance between a[:i] and b[:j]

dp[i][0] = i                                   (delete all of a[:i])
dp[0][j] = j                                   (insert all of b[:j])
dp[i][j] = dp[i-1][j-1]                        if a[i-1] == b[j-1]
         = 1 + min(dp[i-1][j],                 deletion
                    dp[i][j-1],                insertion
                    dp[i-1][j-1])              substitution
```

The implementation uses a rolling single row (`O(min(n, m))` space instead
of a full `O(n*m)` matrix) but is otherwise the textbook algorithm — no
library shortcuts. `distance("kitten", "sitting")` correctly returns `3`
(substitute k→s, substitute e→i, insert g), and `distance("saturday",
"sunday")` returns `3`.

## Why not just brute-force every dictionary word?

A naive spell-checker would compute `distance(query, word)` for every word
in the dictionary and keep the close ones. That's correct but wasteful:
each Levenshtein call is `O(n*m)`, and you pay it thousands of times per
lookup even though most dictionary words are obviously nowhere close.

### The optimization: a BK-tree

Levenshtein distance is a **metric** — it satisfies the triangle
inequality:

```
|d(x, z) - d(y, z)| <= d(x, y) <= d(x, z) + d(y, z)
```

A [BK-tree](https://en.wikipedia.org/wiki/BK-tree) (`bktree.py`) exploits
this directly. Every node's children are keyed by their *exact* distance to
that parent (computed once, at insert time). To search for words within
`max_dist` of a query:

1. Compute `d = distance(query, node.word)` for the current node.
2. If `d <= max_dist`, the node's word is a match.
3. Only descend into a child keyed by `child_dist` if
   `d - max_dist <= child_dist <= d + max_dist`. By the triangle
   inequality, any child outside that range **cannot** contain a match —
   its entire subtree is skipped without ever computing a distance for any
   word in it.

This is a real, measurable pruning of the search space, not brute force
dressed up: on the bundled ~4,275-word dictionary, a lookup that would
otherwise require ~4,275 full edit-distance computations typically needs
only a few hundred to ~2,000, depending on the query and threshold — see
the instrumented tests below.

### Proof it actually prunes

`speller.py` exposes `brute_force_search()` (the naive baseline, computing
distance against every dictionary entry) alongside the `BKTree`-based
`Speller.suggest()`. Both `distance()` and `BKTree.search()` accept an
optional `counter` dict that is incremented once per full edit-distance
computation performed.

`tests/test_bktree_pruning.py` builds one BK-tree from the bundled
dictionary and, for several misspelled queries, runs both strategies with
their own counters, then asserts:

- brute force performs exactly `len(dictionary)` calls (it touches
  everything, by definition), and
- the BK-tree performs **strictly fewer** calls than brute force for every
  tested query, and **less than half** as many for the primary case — this
  is checked directly via the instrumented counts, not inferred from
  timing.

## Word list

`data/wordlist.txt` is a **curated subset for demonstration purposes**, not
an exhaustive English dictionary. Each line is `<word> <frequency>`. It
combines:

- a hand-picked set of ~775 very common English words, ordered and scored
  roughly by real-world frequency (function words like "the"/"of"/"and"
  score highest, down through common nouns, verbs, adjectives, colors,
  animals, family terms, days/months, etc.), and
- a deterministic sample of ~3,500 additional words drawn from the macOS
  system dictionary (`/usr/share/dict/words`) to give the trie and BK-tree
  realistic breadth, each assigned a flat low frequency since there's no
  real usage data backing them.

Total: 4,275 words. This is enough to demonstrate real ranking and
suggestion behavior without needing an external corpus or network access.
Swap in your own `<word> <frequency>` file (or point `Speller` at a
different path) to use a bigger or domain-specific list.

## Case sensitivity

**Design choice: the whole project is case-insensitive.** Every word is
lowercased on insert, and every lookup (`check`, `autocomplete`, `contains`)
lowercases its input before searching. "Cat", "CAT", and "cat" are all the
same entry. This matches how people actually expect spell-check and
autocomplete to behave — nobody wants "Hello" flagged as a different word
from "hello". This is exercised directly in
`tests/test_trie.py::test_case_insensitivity_insert_and_lookup` and
`tests/test_speller.py::test_case_insensitivity_in_check`.

## CLI reference

```bash
python speller.py check <word> [--max-distance N] [--top-k N]
python speller.py autocomplete <prefix> [--limit N]
```

- `check`: prints whether `<word>` is a known dictionary word. If not,
  prints up to `--top-k` (default 5) suggestions within `--max-distance`
  (default 2) edit distance, closest first, frequency as a tiebreaker.
- `autocomplete`: prints up to `--limit` (default 5) dictionary words
  starting with `<prefix>`, most frequent first.

## Tests

`tests/` contains 35 unit tests (stdlib `unittest`, no `pytest` required)
across four files:

- `test_trie.py` — insert/exact lookup, prefix search (all-and-only),
  frequency-ranked autocomplete, empty-prefix handling, case-insensitivity.
- `test_levenshtein.py` — hand-verifiable distances ("kitten"→"sitting" = 3,
  "saturday"→"sunday" = 3), symmetry, edge cases with empty strings.
- `test_bktree_pruning.py` — BK-tree vs. brute-force result agreement, and
  the instrumented call-count comparison proving the pruning is real.
- `test_speller.py` — known-word short-circuit, closest-match-first
  suggestions, frequency tiebreaking, max-distance threshold enforcement,
  case-insensitivity, and graceful handling of empty input.

Run them with:

```bash
python -m unittest discover -s tests -v
```

CI (`.github/workflows/tests.yml`) runs the same suite on every push and
pull request against Python 3.11 and 3.12.

## License

MIT — see [LICENSE](LICENSE).
