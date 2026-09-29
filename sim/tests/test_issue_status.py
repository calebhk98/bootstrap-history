"""Regression tests for sim/issue_status.py.

Written as unittest.TestCase classes (like test_code_health.py): the script
has no dependency on the engine, so importing the harness would only add
cost. Fixtures are small issue trees built in a temporary directory with a
known answer, plus one structural check that the real Complaints/ tree passes
its own check (no counts are asserted, since issues come and go).
"""
import os
import shutil
import sys
import tempfile
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from sim import issue_status  # noqa: E402


class IssueTreeCase(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="issue_status_test_")
        os.makedirs(os.path.join(self.root, "closed"))
        os.makedirs(os.path.join(self.root, "reports"))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write(self, relative_path, text):
        with open(os.path.join(self.root, relative_path), "w", encoding="utf-8") as handle:
            handle.write(text)

    def rows(self):
        return issue_status.collect(self.root)

    def problems(self):
        return issue_status.problems(self.rows())


class ParsingTests(IssueTreeCase):
    def test_reads_title_status_note_and_folder(self):
        self.write("01-a-thing.md", "# A thing\n\n**Status:** partly - half done\n\nbody\n")
        self.write("closed/02-old.md", "# Old thing\n\n**Status:** closed\n")
        rows = self.rows()
        self.assertEqual([row["number"] for row in rows], [1, 2])
        self.assertEqual(rows[0]["title"], "A thing")
        self.assertEqual(rows[0]["status"], "partly")
        self.assertEqual(rows[0]["note"], "half done")
        self.assertEqual(rows[0]["folder"], "open")
        self.assertEqual(rows[1]["folder"], "closed")
        self.assertEqual(self.problems(), [])

    def test_every_valid_status_is_accepted_in_its_folder(self):
        self.write("01-a.md", "# A\n\n**Status:** open\n")
        self.write("02-b.md", "# B\n\n**Status:** partly\n")
        self.write("03-c.md", "# C\n\n**Status:** pinned\n")
        self.write("closed/04-d.md", "# D\n\n**Status:** closed\n")
        self.assertEqual(self.problems(), [])

    def test_ignores_files_that_are_not_numbered_issues(self):
        self.write("README.md", "# Readme\n\nno status here\n")
        self.write("closed/README.md", "# Readme\n")
        self.write("reports/REPORT.md", "# Report\n")
        self.write("TOP_PROBLEMS.md", "# Loose\n")
        self.assertEqual(self.rows(), [])

    def test_blank_lines_between_title_and_status_are_allowed(self):
        self.write("01-a.md", "# A\n\n\n\n**Status:** open\n")
        self.assertEqual(self.problems(), [])


class CheckTests(IssueTreeCase):
    def test_missing_status_line_is_a_problem(self):
        self.write("01-a.md", "# A\n\nJust prose.\n")
        self.assertEqual(len(self.problems()), 1)
        self.assertIn("Status", self.problems()[0])

    def test_status_must_come_right_after_the_title(self):
        self.write("01-a.md", "# A\n\nSome prose first.\n\n**Status:** open\n")
        self.assertEqual(len(self.problems()), 1)

    def test_unknown_status_word_is_a_problem(self):
        self.write("01-a.md", "# A\n\n**Status:** wontfix\n")
        self.assertIn("not one of", self.problems()[0])

    def test_lowercase_marker_or_missing_bold_is_a_problem(self):
        self.write("01-a.md", "# A\n\nStatus: open\n")
        self.write("02-b.md", "# B\n\n**status:** open\n")
        self.assertEqual(len(self.problems()), 2)

    def test_open_status_inside_closed_folder_is_a_problem(self):
        self.write("closed/01-a.md", "# A\n\n**Status:** open\n")
        self.write("closed/02-b.md", "# B\n\n**Status:** partly\n")
        self.assertEqual(len(self.problems()), 2)

    def test_closed_status_outside_closed_folder_is_a_problem(self):
        self.write("01-a.md", "# A\n\n**Status:** closed\n")
        self.assertEqual(len(self.problems()), 1)

    def test_number_used_in_both_folders_is_a_problem(self):
        self.write("05-a.md", "# A\n\n**Status:** open\n")
        self.write("closed/05-b.md", "# B\n\n**Status:** closed\n")
        found = self.problems()
        self.assertEqual(len(found), 1)
        self.assertIn("more than one", found[0])

    def test_clean_tree_has_no_problems_and_missing_folder_is_fine(self):
        shutil.rmtree(os.path.join(self.root, "closed"))
        self.write("01-a.md", "# A\n\n**Status:** open\n")
        self.assertEqual(self.problems(), [])


class OutputTests(IssueTreeCase):
    def test_table_lists_number_title_status_folder(self):
        self.write("07-seven.md", "# Seven\n\n**Status:** pinned\n")
        table = issue_status.format_table(self.rows())
        header, row = table.split("\n")
        for word in ("#", "title", "status", "folder"):
            self.assertIn(word, header)
        for word in ("07", "Seven", "pinned", "open"):
            self.assertIn(word, row)

    def test_counts_cover_every_status(self):
        self.write("01-a.md", "# A\n\n**Status:** open\n")
        self.write("closed/02-b.md", "# B\n\n**Status:** closed\n")
        counts = issue_status.format_counts(self.rows())
        self.assertIn("open 1", counts)
        self.assertIn("closed 1", counts)
        self.assertIn("partly 0", counts)
        self.assertIn("pinned 0", counts)


class RepositoryTreeTests(unittest.TestCase):
    def test_real_complaints_tree_passes_its_own_check(self):
        rows = issue_status.collect()
        self.assertTrue(rows, "no numbered issues found under Complaints/")
        self.assertEqual(issue_status.problems(rows), [])

    def test_check_mode_exit_code_matches_the_tree(self):
        self.assertEqual(issue_status.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
