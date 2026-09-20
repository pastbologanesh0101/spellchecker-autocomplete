import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trie import Trie


class TestTrie(unittest.TestCase):
    def test_insert_and_contains_exact_word(self):
        trie = Trie()
        trie.insert("apple", 10)
        self.assertTrue(trie.contains("apple"))

    def test_contains_false_for_unknown_word(self):
        trie = Trie()
        trie.insert("apple", 10)
        self.assertFalse(trie.contains("banana"))
        # A prefix of an inserted word that was never itself inserted as a
        # complete word should not be reported as "contained".
        self.assertFalse(trie.contains("app"))

    def test_prefix_search_returns_all_and_only_matching_words(self):
        trie = Trie()
        for word in ["cat", "car", "cart", "dog", "do", "card"]:
            trie.insert(word, 1)

        results = {w for w, _freq in trie.words_with_prefix("car")}
        self.assertEqual(results, {"car", "cart", "card"})

        # Words that don't start with the prefix must never appear.
        self.assertNotIn("cat", results)
        self.assertNotIn("dog", results)
        self.assertNotIn("do", results)

    def test_prefix_search_no_matches_returns_empty_list(self):
        trie = Trie()
        trie.insert("hello", 1)
        self.assertEqual(trie.words_with_prefix("xyz"), [])

    def test_autocomplete_ranks_by_frequency_descending(self):
        trie = Trie()
        trie.insert("cart", 5)
        trie.insert("car", 100)
        trie.insert("card", 20)

        ranked_words = [w for w, _freq in trie.autocomplete("car", limit=None)]
        self.assertEqual(ranked_words, ["car", "card", "cart"])

    def test_autocomplete_ties_broken_alphabetically(self):
        trie = Trie()
        trie.insert("bat", 5)
        trie.insert("bad", 5)
        trie.insert("bar", 5)

        ranked_words = [w for w, _freq in trie.autocomplete("ba", limit=None)]
        self.assertEqual(ranked_words, ["bad", "bar", "bat"])

    def test_autocomplete_respects_limit(self):
        trie = Trie()
        for i, word in enumerate(["aa", "ab", "ac", "ad", "ae"]):
            trie.insert(word, 10 - i)
        top_two = trie.autocomplete("a", limit=2)
        self.assertEqual(len(top_two), 2)
        self.assertEqual([w for w, _ in top_two], ["aa", "ab"])

    def test_empty_prefix_returns_full_vocabulary_without_error(self):
        trie = Trie()
        trie.insert("one", 3)
        trie.insert("two", 1)
        # Must not raise, and must include every inserted word.
        results = trie.words_with_prefix("")
        self.assertEqual({w for w, _ in results}, {"one", "two"})

    def test_case_insensitivity_insert_and_lookup(self):
        trie = Trie()
        trie.insert("Apple", 1)
        # Documented behavior: the trie is case-insensitive -- lookups
        # normalize to lowercase, so any casing of an inserted word matches.
        self.assertTrue(trie.contains("apple"))
        self.assertTrue(trie.contains("APPLE"))
        self.assertTrue(trie.contains("ApPlE"))

    def test_repeated_insert_accumulates_frequency(self):
        trie = Trie()
        trie.insert("word", 3)
        trie.insert("word", 4)
        self.assertEqual(trie.get_frequency("word"), 7)


if __name__ == "__main__":
    unittest.main()
