import unittest

from strings import normalize_spaces


class NormalizeSpacesTests(unittest.TestCase):
    def test_trims_and_collapses_whitespace(self):
        self.assertEqual(normalize_spaces("  alpha   beta\n gamma  "), "alpha beta gamma")

    def test_empty_and_whitespace_only(self):
        self.assertEqual(normalize_spaces(""), "")
        self.assertEqual(normalize_spaces(" \t\n "), "")


if __name__ == "__main__":
    unittest.main()
