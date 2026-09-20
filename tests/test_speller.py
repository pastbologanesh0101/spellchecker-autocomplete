import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from speller import Speller

# A small, hand-crafted dictionary so suggestion ordering and thresholds
# are fully predictable (unlike the full few-thousand-word demo list).
CRAFTED_WORDLIST = """
# word frequency
cat 50
cot 10
cart 5
dog 40
dot 8
hello 30
world 25
apple 20
banana 15
zoo 3
"""


def make_speller(wordlist_text=CRAFTED_WORDLIST):
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    try:
        tmp.write(wordlist_text)
    finally:
        tmp.close()
    speller = Speller(wordlist_path=tmp.name)
    os.unlink(tmp.name)
    return speller


class TestSpeller(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.speller = make_speller()

    def test_correctly_spelled_word_reports_known_with_no_suggestions(self):
        result = self.speller.check("cat")
        self.assertTrue(result["known"])
        self.assertEqual(result["suggestions"], [])

    def test_misspelled_word_returns_genuinely_closest_match_first(self):
        # "caat" is distance 1 from "cat" and distance 2+ from everything
        # else in the crafted dictionary, so "cat" must rank first.
        result = self.speller.check("caat", max_dist=2, top_k=3)
        self.assertFalse(result["known"])
        self.assertTrue(result["suggestions"])
        top_word, top_dist, _freq = result["suggestions"][0]
        self.assertEqual(top_word, "cat")
        self.assertEqual(top_dist, 1)

    def test_suggestions_use_frequency_as_tiebreaker(self):
        # "cbt" is distance 1 from both "cat" (freq 50) and "cot" (freq 10).
        # Frequency should break the tie in favor of "cat".
        result = self.speller.check("cbt", max_dist=1, top_k=5)
        candidates_at_min_distance = [
            (w, f) for w, d, f in result["suggestions"] if d == 1
        ]
        self.assertIn("cat", [w for w, _ in candidates_at_min_distance])
        self.assertIn("cot", [w for w, _ in candidates_at_min_distance])
        # cat (freq 50) must be ranked ahead of cot (freq 10).
        ranked = [w for w, _f in candidates_at_min_distance]
        self.assertLess(ranked.index("cat"), ranked.index("cot"))

    def test_max_distance_threshold_excludes_unrelated_words(self):
        # "zoo" only appears in the crafted dictionary far from "hello" --
        # with a tight threshold nothing wildly unrelated should surface.
        result = self.speller.check("helllo", max_dist=1, top_k=5)
        suggested_words = {w for w, _d, _f in result["suggestions"]}
        self.assertIn("hello", suggested_words)
        self.assertNotIn("zoo", suggested_words)
        self.assertNotIn("banana", suggested_words)
        for _w, d, _f in result["suggestions"]:
            self.assertLessEqual(d, 1)

    def test_case_insensitivity_in_check(self):
        # Documented behavior: input is lowercased before lookup, so
        # "CAT", "Cat" and "cat" are all treated as the known word "cat".
        for variant in ["CAT", "Cat", "cAt"]:
            with self.subTest(variant=variant):
                result = self.speller.check(variant)
                self.assertTrue(result["known"])
                self.assertEqual(result["word"], "cat")

    def test_empty_word_handled_gracefully(self):
        result = self.speller.check("")
        self.assertFalse(result["known"])
        self.assertEqual(result["suggestions"], [])
        self.assertTrue(result["empty"])

    def test_empty_prefix_autocomplete_handled_gracefully(self):
        # Must not raise, and should return a ranked (non-empty) list
        # rather than silently doing nothing.
        matches = self.speller.autocomplete("", limit=3)
        self.assertEqual(len(matches), 3)
        # Highest-frequency word in the crafted dictionary is "cat" (50).
        self.assertEqual(matches[0][0], "cat")

    def test_autocomplete_frequency_ordering_via_speller(self):
        # Prefix "c" matches "cat" (50), "cot" (10), "cart" (5).
        matches = self.speller.autocomplete("c", limit=None)
        self.assertEqual([w for w, _f in matches], ["cat", "cot", "cart"])

    def test_is_known_is_case_insensitive_and_false_for_unknown(self):
        self.assertTrue(self.speller.is_known("Dog"))
        self.assertFalse(self.speller.is_known("giraffe"))


if __name__ == "__main__":
    unittest.main()
