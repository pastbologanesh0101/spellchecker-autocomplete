"""
BK-tree (Burkhard-Keller tree) for approximate nearest-neighbor search
under an arbitrary metric distance function -- here, Levenshtein edit
distance.

Why a BK-tree instead of brute force?
--------------------------------------
Levenshtein distance is a *metric*: it obeys the triangle inequality,
    |d(x, z) - d(y, z)| <= d(x, y) <= d(x, z) + d(y, z)
A BK-tree exploits this: every node's children are keyed by their exact
distance to their parent. When searching for words within `max_dist` of a
query, we compute the distance from the query to a node once, and then use
the triangle inequality to discard entire subtrees whose keyed distance
could not possibly produce a result within `max_dist` -- without ever
computing the (expensive) edit distance for any word in that subtree.

That is the measurable optimization this project demonstrates: a plain
brute-force scan computes `distance()` once per dictionary word, while a
BK-tree search computes it only for nodes it cannot rule out ahead of
time. See tests/test_bktree_pruning.py for a direct comparison of the
number of `distance()` calls each strategy performs over the same
dictionary.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple


class BKNode:
    __slots__ = ("word", "frequency", "children")

    def __init__(self, word: str, frequency: int) -> None:
        self.word = word
        self.frequency = frequency
        self.children: Dict[int, "BKNode"] = {}


DistanceFn = Callable[..., int]


class BKTree:
    def __init__(self, distance_fn: DistanceFn) -> None:
        self.distance_fn = distance_fn
        self.root: Optional[BKNode] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def insert(self, word: str, frequency: int = 1, counter: Optional[Dict[str, int]] = None) -> None:
        if not word:
            return
        if self.root is None:
            self.root = BKNode(word, frequency)
            self._size += 1
            return

        node = self.root
        while True:
            d = self.distance_fn(word, node.word, counter)
            if d == 0:
                # Same word already present -- merge frequency instead of
                # creating a duplicate node.
                node.frequency += frequency
                return
            child = node.children.get(d)
            if child is None:
                node.children[d] = BKNode(word, frequency)
                self._size += 1
                return
            node = child

    def search(
        self,
        word: str,
        max_dist: int,
        counter: Optional[Dict[str, int]] = None,
    ) -> List[Tuple[str, int, int]]:
        """Return every (word, distance, frequency) with distance <= max_dist.

        `counter`, if provided, has `counter["calls"]` incremented once per
        `distance_fn` invocation performed during this search -- used to
        measure how many full edit-distance computations were needed.
        """
        if self.root is None or not word:
            return []

        results: List[Tuple[str, int, int]] = []
        stack: List[BKNode] = [self.root]

        while stack:
            node = stack.pop()
            d = self.distance_fn(word, node.word, counter)
            if d <= max_dist:
                results.append((node.word, d, node.frequency))

            # Triangle inequality prune: only descend into a child keyed by
            # `child_dist` (the exact distance from `node` to `child` when
            # it was inserted) if it's still possible for that child's
            # subtree to contain a match within max_dist of `word`.
            lo, hi = d - max_dist, d + max_dist
            for child_dist, child in node.children.items():
                if lo <= child_dist <= hi:
                    stack.append(child)

        return results
