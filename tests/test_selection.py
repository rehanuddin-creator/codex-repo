import unittest

from auto_software_installer import parse_selection, resolve_software_list


class SelectionTests(unittest.TestCase):
    def test_parse_selection_keeps_order_and_unique(self):
        self.assertEqual(parse_selection("1,3,1,2", 4), [1, 3, 2])

    def test_parse_selection_rejects_out_of_range(self):
        with self.assertRaises(ValueError):
            parse_selection("0", 3)

    def test_resolve_software_list_removes_duplicates(self):
        self.assertEqual(
            resolve_software_list("git,curl,git"),
            ["git", "curl"],
        )

    def test_resolve_software_list_rejects_unknown(self):
        with self.assertRaises(ValueError):
            resolve_software_list("git,unknown")


if __name__ == "__main__":
    unittest.main()
