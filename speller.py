#!/usr/bin/env python3
"""
Spell Checker & Autocomplete
=============================

A from-scratch, pure-stdlib demonstration of:
  * a Trie for prefix-based autocomplete, ranked by word frequency
  * Levenshtein edit distance (dynamic programming) for spell-check
    suggestions
  * a BK-tree over that Levenshtein metric so spell-check suggestion
    search doesn't have to brute-force every dictionary word

See README.md for a full explanation of the data structures and the
pruning optimization. See tests/ for correctness and performance tests.

CLI usage:
    python speller.py check <word>
    python speller.py autocomplete <prefix>
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, List, Optional, Tuple

from bktree import BKTree
from levenshtein import distance as levenshtein_distance
from trie import Trie

DEFAULT_WORDLIST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "wordlist.txt")
DEFAULT_MAX_DISTANCE = 2
DEFAULT_TOP_K = 5


def load_wordlist(path: str) -> List[Tuple[str, int]]:
    """Parse a `<word> <frequency>` per line file (frequency optional, '#'
    lines and blank lines ignored) into a list of (word, frequency) pairs.
    """
    entries: List[Tuple[str, int]] = []
    with open(path, encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            word = parts[0].lower()
            frequency = int(parts[1]) if len(parts) > 1 else 1
            entries.append((word, frequency))
    return entries


def brute_force_search(
    dictionary: List[Tuple[str, int]],
    word: str,
    max_dist: int,
    counter: Optional[Dict[str, int]] = None,
) -> List[Tuple[str, int, int]]:
    """Reference/baseline implementation: compute the full edit distance
    between `word` and *every* entry in `dictionary`, keeping the ones
    within `max_dist`. Used both as a correctness cross-check and as the
    "before" side of the pruning-optimization comparison.
    """
    results: List[Tuple[str, int, int]] = []
    for candidate, frequency in dictionary:
        d = levenshtein_distance(word, candidate, counter)
        if d <= max_dist:
            results.append((candidate, d, frequency))
    return results


class Speller:
    """Ties the Trie (exact lookup + autocomplete) and BK-tree
    (approximate/spell-check search) together over one loaded dictionary.
    """

    def __init__(self, wordlist_path: str = DEFAULT_WORDLIST_PATH) -> None:
        self.wordlist_path = wordlist_path
        self.trie = Trie()
        self.bktree = BKTree(levenshtein_distance)
        self._entries: List[Tuple[str, int]] = load_wordlist(wordlist_path)
        for word, frequency in self._entries:
            self.trie.insert(word, frequency)
        # Build the BK-tree from the trie's merged (word, frequency) pairs
        # so duplicate lines in the wordlist are already summed.
        for word, frequency in self.trie.items():
            self.bktree.insert(word, frequency)

    @property
    def dictionary(self) -> List[Tuple[str, int]]:
        """All (word, frequency) pairs currently known, from the trie."""
        return self.trie.items()

    def is_known(self, word: str) -> bool:
        return self.trie.contains(word)

    def autocomplete(self, prefix: str, limit: Optional[int] = DEFAULT_TOP_K) -> List[Tuple[str, int]]:
        return self.trie.autocomplete(prefix, limit)

    def suggest(
        self,
        word: str,
        max_dist: int = DEFAULT_MAX_DISTANCE,
        top_k: int = DEFAULT_TOP_K,
        counter: Optional[Dict[str, int]] = None,
    ) -> List[Tuple[str, int, int]]:
        """Return up to `top_k` (word, distance, frequency) suggestions for
        `word`, sorted by distance ascending then frequency descending
        (closer matches first; among equally-close matches, the more
        common word first).
        """
        word = (word or "").lower()
        if not word:
            return []
        candidates = self.bktree.search(word, max_dist, counter=counter)
        candidates.sort(key=lambda c: (c[1], -c[2], c[0]))
        return candidates[:top_k]

    def check(
        self,
        word: str,
        max_dist: int = DEFAULT_MAX_DISTANCE,
        top_k: int = DEFAULT_TOP_K,
    ) -> Dict[str, object]:
        """Spell-check `word`. Returns a dict with:
            word: the (lowercased) word that was checked
            known: True if it's an exact dictionary match
            suggestions: [] if known, else up to top_k (word, distance, frequency)
        """
        original = word
        word_l = (word or "").strip().lower()
        if not word_l:
            return {"word": original, "known": False, "suggestions": [], "empty": True}
        if self.trie.contains(word_l):
            return {"word": word_l, "known": True, "suggestions": [], "empty": False}
        suggestions = self.suggest(word_l, max_dist=max_dist, top_k=top_k)
        return {"word": word_l, "known": False, "suggestions": suggestions, "empty": False}


def _format_check(result: Dict[str, object]) -> str:
    if result.get("empty"):
        return "(empty input -- nothing to check)"
    word = result["word"]
    if result["known"]:
        return f'"{word}" is a known word.'
    suggestions = result["suggestions"]
    if not suggestions:
        return f'"{word}" is NOT a known word, and no close suggestions were found.'
    lines = [f'"{word}" is NOT a known word. Did you mean:']
    for i, (candidate, dist, freq) in enumerate(suggestions, start=1):
        lines.append(f"  {i}. {candidate}  (edit distance {dist}, frequency {freq})")
    return "\n".join(lines)


def _format_autocomplete(prefix: str, matches: List[Tuple[str, int]]) -> str:
    if not prefix:
        header = "(empty prefix -- showing most frequent words overall)"
    else:
        header = f'Completions for "{prefix}":'
    if not matches:
        return f"{header}\n  (no matches)"
    lines = [header]
    for i, (word, freq) in enumerate(matches, start=1):
        lines.append(f"  {i}. {word}  (frequency {freq})")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="speller.py",
        description="Trie-based autocomplete + Levenshtein spell-checker.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_parser = subparsers.add_parser("check", help="Spell-check a word.")
    check_parser.add_argument("word", help="The word to check.")
    check_parser.add_argument("--max-distance", type=int, default=DEFAULT_MAX_DISTANCE)
    check_parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)

    auto_parser = subparsers.add_parser("autocomplete", help="Autocomplete a prefix.")
    auto_parser.add_argument("prefix", help="The prefix to complete.")
    auto_parser.add_argument("--limit", type=int, default=DEFAULT_TOP_K)

    args = parser.parse_args(argv)

    speller = Speller()

    if args.command == "check":
        result = speller.check(args.word, max_dist=args.max_distance, top_k=args.top_k)
        print(_format_check(result))
    elif args.command == "autocomplete":
        matches = speller.autocomplete(args.prefix, limit=args.limit)
        print(_format_autocomplete(args.prefix, matches))

    return 0


if __name__ == "__main__":
    sys.exit(main())
