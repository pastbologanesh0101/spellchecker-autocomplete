import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bktree import BKTree
from levenshtein import distance
from speller import DEFAULT_WORDLIST_PATH, brute_force_search, load_wordlist


class TestBKTreePruning(unittest.TestCase):
    """Verifies that the BK-tree is not just *correct* but actually does
    less work than a brute-force scan over the same dictionary, by
    instrumenting the number of full Levenshtein computations each
    strategy performs.
    """

    @classmethod
    def setUpClass(cls):
        cls.entries = load_wordlist(DEFAULT_WORDLIST_PATH)
        cls.tree = BKTree(distance)
        for word, freq in cls.entries:
            # No counter here -- tree construction cost isn't part of the
            # search-time comparison below.
            cls.tree.insert(word, freq)

    def test_bktree_and_brute_force_agree_on_results(self):
        query = "wrold"
        max_dist = 2

        bktree_words = {word for word, _dist, _freq in self.tree.search(query, max_dist)}
        brute_words = {word for word, _dist, _freq in brute_force_search(self.entries, query, max_dist)}

        self.assertEqual(bktree_words, brute_words)
        self.assertIn("world", bktree_words)

    def test_bktree_prunes_measurably_fewer_edit_distance_calls(self):
        query = "wrold"
        max_dist = 2

        bktree_counter = {}
        self.tree.search(query, max_dist, counter=bktree_counter)

        brute_counter = {}
        brute_force_search(self.entries, query, max_dist, counter=brute_counter)

        # Brute force must touch every dictionary entry exactly once.
        self.assertEqual(brute_counter["calls"], len(self.entries))

        # The BK-tree must perform strictly fewer full edit-distance
        # computations than brute force over the same dictionary and query.
        self.assertLess(bktree_counter["calls"], brute_counter["calls"])

        # The pruning should be substantial, not a rounding error: over a
        # dictionary of several thousand words, the BK-tree should need to
        # examine well under half of them.
        self.assertLess(bktree_counter["calls"], brute_counter["calls"] * 0.5)

    def test_bktree_prunes_across_multiple_queries(self):
        # Same measurable-pruning property, checked for several different
        # queries/thresholds so it isn't a fluke of one word.
        for query, max_dist in [("speling", 2), ("recieve", 2), ("definately", 3), ("wierd", 1)]:
            bktree_counter = {}
            self.tree.search(query, max_dist, counter=bktree_counter)
            brute_counter = {}
            brute_force_search(self.entries, query, max_dist, counter=brute_counter)
            with self.subTest(query=query, max_dist=max_dist):
                self.assertLess(bktree_counter["calls"], brute_counter["calls"])

    def test_bktree_respects_max_distance_threshold(self):
        # "zzzzzzzzzzzz" is nowhere near any real dictionary word; with a
        # tight threshold, nothing should be returned.
        results = self.tree.search("zzzzzzzzzzzz", max_dist=1)
        self.assertEqual(results, [])

    def test_bktree_empty_query_handled_gracefully(self):
        # Must not raise, and must not spuriously match everything.
        self.assertEqual(self.tree.search("", max_dist=3), [])

    def test_bktree_empty_tree_handled_gracefully(self):
        empty_tree = BKTree(distance)
        self.assertEqual(empty_tree.search("anything", max_dist=5), [])


if __name__ == "__main__":
    unittest.main()
