"""Topics are discovered from sim/tests/test_*.py, never registered by hand.

Drops fresh test files into a scratch copy of the tests directory and checks
that discovery finds them, sorts them, and reads the per-file QUICK_TOPIC marker.
"""

QUICK_TOPIC = True

import shutil
import tempfile

from .harness import *
from . import harness as _harness

_scratch_root = tempfile.mkdtemp(prefix="topic_discovery_")
try:
    _scratch_dir = os.path.join(_scratch_root, "tests")
    shutil.copytree(os.path.join(HERE, "tests"), _scratch_dir,
                    ignore=shutil.ignore_patterns("__pycache__"))
    with open(os.path.join(_scratch_dir, "test_zz_brand_new.py"), "w") as _handle:
        _handle.write('"""New topic."""\nQUICK_TOPIC = True\n')
    with open(os.path.join(_scratch_dir, "test_aa_brand_new.py"), "w") as _handle:
        _handle.write('"""New topic."""\nQUICK_TOPIC = False\n')
    # Near misses that must not become topics.
    for _decoy in ("helper_test.py", "testing_notes.py", "test_notes.txt"):
        with open(os.path.join(_scratch_dir, _decoy), "w") as _handle:
            _handle.write("")

    _found = _harness.discover_topics(_scratch_dir)
    _quick = _harness.discover_quick_topics(_scratch_dir)
    check("a new test_*.py is discovered as a topic with no registration",
          "zz_brand_new" in _found and "aa_brand_new" in _found, _found[-3:])
    check("discovery ignores files that only resemble test modules",
          not {"notes", "helper_test", "testing_notes"} & set(_found), _found)
    check("discovery order is deterministic (sorted by name)",
          _found == sorted(_found), "not sorted")
    check("QUICK_TOPIC = True in a file puts that topic in the quick tier, and only that one",
          "zz_brand_new" in _quick and "aa_brand_new" not in _quick, _quick)
finally:
    shutil.rmtree(_scratch_root, ignore_errors=True)

check("the real tests directory yields every test_*.py as a topic",
      _harness.discover_topics() == sorted(
          name[len("test_"):-len(".py")] for name in os.listdir(os.path.join(HERE, "tests"))
          if name.startswith("test_") and name.endswith(".py")))
