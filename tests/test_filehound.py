import tempfile
import unittest
from pathlib import Path
from filehound import find_duplicates

class FileHoundTests(unittest.TestCase):
    def test_finds_same_content(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one.txt").write_text("same", encoding="utf-8")
            (root / "two.txt").write_text("same", encoding="utf-8")
            groups, errors = find_duplicates([root])
            self.assertFalse(errors)
            self.assertEqual(len(groups), 1)
            self.assertEqual(len(groups[0]["paths"]), 2)

    def test_different_content_is_not_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "one.txt").write_text("first", encoding="utf-8")
            (root / "two.txt").write_text("other", encoding="utf-8")
            groups, _ = find_duplicates([root])
            self.assertEqual(groups, [])

if __name__ == "__main__":
    unittest.main()
