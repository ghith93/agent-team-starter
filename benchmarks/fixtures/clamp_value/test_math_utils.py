import unittest

from math_utils import clamp


class ClampTests(unittest.TestCase):
    def test_clamps_both_bounds(self):
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_preserves_values_inside_range(self):
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_rejects_inverted_bounds(self):
        with self.assertRaises(ValueError):
            clamp(5, 10, 0)


if __name__ == "__main__":
    unittest.main()
