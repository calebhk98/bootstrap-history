#!/usr/bin/env python3
"""issue_status.py: the status table for every numbered issue in Complaints/.

    python3 sim/issue_status.py                table of every issue
    python3 sim/issue_status.py --status open  only issues with that status
    python3 sim/issue_status.py --check        exit non-zero on a malformed
                                               status line or a wrong folder
    python3 sim/issue_status.py --json         the same rows as JSON
    python3 sim/issue_status.py --next         the next free number
    python3 sim/issue_status.py --renumber     report the old -> new map that
                                               closes gaps and duplicates
                                               (--write applies it)

Each issue file is `NN-slug.md`, in `Complaints/` (not finished) or
`Complaints/closed/` (finished). Its first line is the title and the first
non-blank line after that is the status line:

    **Status:** open | partly | pinned | closed
    **Status:** partly - one short note

Nothing else keeps this list, so it cannot go stale: the files are the data.
Files that are not numbered issues (READMEs, `reports/`) are ignored.
"""
import argparse
import json
import os
import re
import sys

try:
    from sim import issue_renumber
except ImportError:
    import issue_renumber

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPLAINTS_DIR = os.path.join(REPO_ROOT, "Complaints")
CLOSED_DIRNAME = "closed"

VALID_STATUSES = ("open", "partly", "pinned", "closed")
# Statuses a file may have while it sits in each folder.
STATUSES_BY_FOLDER = {
    "open": ("open", "partly", "pinned"),
    CLOSED_DIRNAME: ("closed",),
}

_FILENAME = re.compile(r"^(\d+)-.+\.md$")
_STATUS_LINE = re.compile(r"^\*\*Status:\*\* (\w+)(?: - (.+))?$")


def _first_lines(path):
    """The title, and the first non-blank line after it (or None)."""
    with open(path, encoding="utf-8") as handle:
        lines = handle.read().split("\n")
    title = lines[0].lstrip("# ").strip() if lines else ""
    for line in lines[1:]:
        if line.strip():
            return title, line.strip()
    return title, None


def read_issue(path, folder):
    """One issue file as a row. `problem` is None when the file is well formed."""
    name = os.path.basename(path)
    number = int(_FILENAME.match(name).group(1))
    title, status_line = _first_lines(path)
    row = {"number": number, "file": name, "title": title, "folder": folder,
           "status": None, "note": "", "problem": None}
    match = _STATUS_LINE.match(status_line) if status_line else None
    if not match:
        row["problem"] = "no `**Status:** <status>` line right after the title"
        return row
    row["status"] = match.group(1)
    row["note"] = match.group(2) or ""
    if row["status"] not in VALID_STATUSES:
        row["problem"] = "status %r is not one of %s" % (row["status"], ", ".join(VALID_STATUSES))
    elif row["status"] not in STATUSES_BY_FOLDER[folder]:
        row["problem"] = "status %r does not belong in the %s folder" % (
            row["status"], "closed/" if folder == CLOSED_DIRNAME else "top-level")
    return row


def collect(complaints_dir=COMPLAINTS_DIR):
    """Every numbered issue in both folders, sorted by number.

    A number used twice (in either folder) is reported on the later file.
    """
    rows = []
    for folder, directory in (("open", complaints_dir),
                              (CLOSED_DIRNAME, os.path.join(complaints_dir, CLOSED_DIRNAME))):
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if _FILENAME.match(name):
                rows.append(read_issue(os.path.join(directory, name), folder))
    rows.sort(key=lambda row: (row["number"], row["folder"]))
    seen = set()
    for row in rows:
        if row["number"] in seen and not row["problem"]:
            row["problem"] = "number %d is used by more than one file" % row["number"]
        seen.add(row["number"])
    return rows


def problems(rows):
    return ["%s (%s): %s" % (row["file"], row["folder"], row["problem"])
            for row in rows if row["problem"]]


def numbering_problems(rows):
    """Numbers must be exactly 1..N: report duplicates and gaps."""
    numbers = [row["number"] for row in rows]
    found = ["number %d is used by more than one file" % number
             for number in sorted(set(numbers)) if numbers.count(number) > 1]
    if sorted(set(numbers)) != list(range(1, len(set(numbers)) + 1)):
        found.append("numbers are not 1..N without gaps; run `--renumber --write`")
    return found


def next_number(rows):
    """The next free number: one above the highest in use (the count, when numbering has no gaps)."""
    return max([row["number"] for row in rows] + [0]) + 1


def format_table(rows):
    header = ("#", "title", "status", "folder")
    body = [("%02d" % row["number"], row["title"], row["status"] or "?", row["folder"])
            for row in rows]
    widths = [max(len(str(line[column])) for line in [header] + body) for column in range(4)]
    widths[1] = min(widths[1], 72)
    lines = []
    for line in [header] + body:
        title = line[1] if len(line[1]) <= widths[1] else line[1][:widths[1] - 3] + "..."
        lines.append("  ".join([str(line[0]).ljust(widths[0]), title.ljust(widths[1]),
                                str(line[2]).ljust(widths[2]), str(line[3])]))
    return "\n".join(lines)


def format_counts(rows):
    counts = {status: 0 for status in VALID_STATUSES}
    for row in rows:
        if row["status"] in counts:
            counts[row["status"]] += 1
    return "  ".join("%s %d" % (status, counts[status]) for status in VALID_STATUSES)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Status table for Complaints/.")
    parser.add_argument("--check", action="store_true",
                        help="print problems and exit non-zero if there are any")
    parser.add_argument("--status", choices=VALID_STATUSES,
                        help="show only issues with this status")
    parser.add_argument("--json", action="store_true", help="print rows as JSON")
    parser.add_argument("--next", action="store_true", help="print the next free number")
    parser.add_argument("--renumber", action="store_true",
                        help="report how numbers would change to run 1..N, rewriting references")
    parser.add_argument("--write", action="store_true", help="with --renumber: apply it")
    args = parser.parse_args(argv)

    rows = collect()
    if args.next:
        print(next_number(rows))
        return 0
    if args.renumber:
        result = issue_renumber.plan(REPO_ROOT, rows)
        print(issue_renumber.report(result))
        if args.write:
            issue_renumber.apply(REPO_ROOT, result)
            print("written; old -> new map in Complaints/RENUMBERED.md")
        return 0
    found = problems(rows)
    if args.check:
        found = found + numbering_problems(rows)
        for problem in found:
            print(problem)
        if not found:
            print("ok: every issue file has a valid status line in the right folder, numbered 1..%d"
                  % len(rows))
        return 1 if found else 0

    shown = [row for row in rows if not args.status or row["status"] == args.status]
    if args.json:
        print(json.dumps(shown, indent=2))
    else:
        print(format_table(shown))
        print()
        print(format_counts(rows))
        for problem in found:
            print("PROBLEM: " + problem)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
