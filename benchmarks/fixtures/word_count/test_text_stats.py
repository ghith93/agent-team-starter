import unittest

from text_stats import word_count


class WordCountTests(unittest.TestCase):
    def test_counts_arbitrary_whitespace(self):
        self.assertEqual(word_count("one  two\tthree\nfour"), 4)

    def test_empty_input_has_zero_words(self):
        self.assertEqual(word_count(""), 0)
        self.assertEqual(word_count("   \n\t "), 0)


if __name__ == "__main__":
    unittest.main()
