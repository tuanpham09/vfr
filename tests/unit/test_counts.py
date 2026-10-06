import math
import unittest

from core.pipeline.counts import parse_count

CASES = [
    (1234, (1234, False)), ("1234", (1234, False)), ("1,234", (1234, False)), (0, (0, False)), ("0", (0, False)),
    ("1.2万", (12000, True)), ("1.2w", (12000, True)), ("1.2W", (12000, True)), ("3.5亿", (350000000, True)),
    ("1.2K", (1200, True)), ("3.4M", (3400000, True)), ("2B", (2000000000, True)), ("2.3k", (2300, True)),
    ("1,5K", (1500, True)), ("10+", (10, True)), ("1000+", (1000, True)), (12.0, (12, False)), (3.6, (4, False)),
    ("赞", (None, False)), ("点赞", (None, False)), ("", (None, False)), (None, (None, False)),
    (-5, (None, False)), ("-5", (None, False)), (float("nan"), (None, False)), (float("inf"), (None, False)),
    ("abc", (None, False)), (True, (None, False)), ([], (None, False)), ({}, (None, False)),
    ("  7万 ", (70000, True)),
]


class TestCounts(unittest.TestCase):
    def test_table(self):
        for inp, exp in CASES:
            with self.subTest(inp=inp):
                self.assertEqual(parse_count(inp), exp)

    def test_never_raises(self):
        for v in ["9" * 400, "1e999", "١٢٣", object(), "1.2.3万", "万", ".5", "5."]:
            r = parse_count(v)
            self.assertIsInstance(r, tuple)
            self.assertEqual(len(r), 2)


if __name__ == "__main__":
    unittest.main()
