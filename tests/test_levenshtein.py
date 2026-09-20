import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from levenshtein import distance


class TestLevenshtein(unittest.TestCase):
    def test_kitten_sitting_is_three(self):
        # The classic textbook example.
        self.assertEqual(distance("kitten", "sitting"), 3)

    def test_saturday_sunday_is_three(self):
        # Another well-known hand-verifiable example.
        self.assertEqual(distance("saturday", "sunday"), 3)

    def test_identical_strings_have_zero_distance(self):
        self.assertEqual(distance("hello", "hello"), 0)

    def test_distance_to_empty_string_equals_length(self):
        self.assertEqual(distance("", "abc"), 3)
        self.assertEqual(distance("abc", ""), 3)
        self.assertEqual(distance("", ""), 0)

    def test_single_substitution(self):
        self.assertEqual(distance("cat", "cap"), 1)

    def test_single_insertion(self):
        self.assertEqual(distance("cat", "cats"), 1)

    def test_single_deletion(self):
        self.assertEqual(distance("cats", "cat"), 1)

    def test_distance_is_symmetric(self):
        self.assertEqual(distance("flaw", "lawn"), distance("lawn", "flaw"))
        self.assertEqual(distance("flaw", "lawn"), 2)

    def test_completely_different_strings(self):
        # No shared characters at all -> distance equals the longer length
        # when lengths differ, or equal to the length when substituting
        # every character for same-length strings.
        self.assertEqual(distance("abc", "xyz"), 3)

    def test_counter_increments_once_per_call(self):
        counter = {}
        distance("abc", "abd", counter)
        distance("abc", "xyz", counter)
        self.assertEqual(counter["calls"], 2)


if __name__ == "__main__":
    unittest.main()
