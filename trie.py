"""
A simple Trie (prefix tree) for storing English words with per-word
frequency counts.

Case-insensitivity: all words are lowercased on insert and on lookup, so
"Cat", "cat" and "CAT" are treated as the same word throughout this
project. This keeps the trie small (one node path per spelling instead of
duplicating case variants) and matches how autocomplete/spell-check is
used in practice -- users don't expect case to matter.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Tuple


class TrieNode:
    __slots__ = ("children", "is_word", "frequency")

    def __init__(self) -> None:
        self.children: dict[str, "TrieNode"] = {}
        self.is_word: bool = False
        self.frequency: int = 0


class Trie:
    """A prefix tree mapping words -> frequency counts."""

    def __init__(self) -> None:
        self.root = TrieNode()
        self._size = 0

    def insert(self, word: str, frequency: int = 1) -> None:
        """Insert a word with the given frequency.

        Inserting the same word again ADDS to its existing frequency,
        rather than overwriting it -- this mirrors how a real frequency
        table would be built up from repeated observations.
        """
        if not word:
            return
        word = word.lower()
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        if not node.is_word:
            self._size += 1
        node.is_word = True
        node.frequency += frequency

    def contains(self, word: str) -> bool:
        """Return True iff `word` was inserted (exact match, case-insensitive)."""
        if not word:
            return False
        node = self._find_node(word.lower())
        return node is not None and node.is_word

    def get_frequency(self, word: str) -> int:
        """Return the stored frequency for `word`, or 0 if unknown."""
        if not word:
            return 0
        node = self._find_node(word.lower())
        if node is not None and node.is_word:
            return node.frequency
        return 0

    def __len__(self) -> int:
        return self._size

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        node = self.root
        for ch in prefix:
            node = node.children.get(ch)
            if node is None:
                return None
        return node

    def words_with_prefix(self, prefix: str) -> List[Tuple[str, int]]:
        """Return every (word, frequency) pair for words starting with `prefix`.

        An empty prefix matches every word in the trie (there is nothing
        wrong with that request -- it just means "list everything").
        """
        prefix = (prefix or "").lower()
        start_node = self._find_node(prefix) if prefix else self.root
        if start_node is None:
            return []
        results: List[Tuple[str, int]] = []
        self._collect(start_node, prefix, results)
        return results

    def _collect(self, node: TrieNode, path: str, results: List[Tuple[str, int]]) -> None:
        if node.is_word:
            results.append((path, node.frequency))
        for ch in sorted(node.children):
            self._collect(node.children[ch], path + ch, results)

    def autocomplete(self, prefix: str, limit: Optional[int] = 5) -> List[Tuple[str, int]]:
        """Return up to `limit` (word, frequency) completions for `prefix`,
        ranked by frequency descending, then alphabetically for ties.

        `limit=None` returns every match. An empty prefix is handled
        gracefully by returning the whole (ranked) vocabulary rather than
        raising an error.
        """
        matches = self.words_with_prefix(prefix)
        matches.sort(key=lambda wf: (-wf[1], wf[0]))
        if limit is None:
            return matches
        return matches[:limit]

    def all_words(self) -> List[str]:
        return [w for w, _ in self.words_with_prefix("")]

    def items(self) -> Iterable[Tuple[str, int]]:
        return self.words_with_prefix("")
