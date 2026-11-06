#!/usr/bin/env python3
"""Import every non-test module under sim/ in a fresh interpreter of its own and report each that fails with an
ImportError (an import cycle or a name that moved). A module missing only a third-party package is skipped.
Exit status is the number of failures, capped at one."""
import concurrent.futures
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def module_names():
    names = []
    for directory, subdirectories, files in os.walk(os.path.join(ROOT, "sim")):
        subdirectories[:] = sorted(each for each in subdirectories if each not in ("tests", "__pycache__"))
        for filename in sorted(files):
            if not filename.endswith(".py") or filename == "__main__.py":
                continue
            relative = os.path.relpath(os.path.join(directory, filename[:-3]), ROOT)
            name = relative.replace(os.sep, ".")
            names.append(name[:-len(".__init__")] if name.endswith(".__init__") else name)
    return sorted(names)


def import_alone(name):
    """The last line of the error when `import name` fails alone in a fresh interpreter, else None."""
    result = subprocess.run([sys.executable, "-c", "import " + name], cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        return None
    lines = result.stderr.strip().splitlines()
    last = lines[-1] if lines else "failed with no message"
    if last.startswith("ModuleNotFoundError") and "'sim" not in last:
        return None
    return last


def main():
    names = module_names()
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        errors = list(pool.map(import_alone, names))
    failed = [(name, error) for name, error in zip(names, errors) if error]
    for name, error in failed:
        print("%s: %s" % (name, error))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
