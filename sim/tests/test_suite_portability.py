"""The suite must run from a checkout of any name, in any directory: the harness's ROOT is the checkout itself, so a path
joined onto it addresses this checkout's data, and scratch directories are created inside it. The run itself from a renamed
root is test_suite_portability_smoke."""
QUICK_TOPIC = True

import os

from .harness import *
from .harness import ROOT, HERE, _LOADTEST_DIR, _PLAY_DIR


# --- ROOT means the repository, not something near it. Every relative path in
# this package is joined onto ROOT, so if ROOT drifts one level the joins do
# not error, they simply address nothing.
check("harness.ROOT is the repository root, so os.path.join(ROOT, 'data') "
      "addresses this checkout's own data",
      all(os.path.isdir(os.path.join(ROOT, directory))
          for directory in ("data", "sim", "docs", "playtest")),
      ROOT)

check("...and it is THIS checkout, the one the harness itself was imported "
      "from, not another copy that happens to be nearby",
      os.path.abspath(os.path.join(ROOT, "sim")) == os.path.abspath(HERE),
      (ROOT, HERE))

check("the civilization glob that silently matched nothing now matches every "
      "civilization file",
      len([filename for filename
           in os.listdir(os.path.join(ROOT, "data", "civilizations"))
           if filename.endswith(".json") and not filename.startswith("_")]) >= 5,
      sorted(os.listdir(os.path.join(ROOT, "data", "civilizations"))))


# --- Scratch belongs inside the checkout. When ROOT was the parent, a test run
# wrote _loadtest_tmp and _playtest_tmp into whatever directory the checkout
# happened to sit in - someone's home directory, a CI workspace root - where no
# .gitignore covered them and nobody thought to look.
for _scratch in (_LOADTEST_DIR, _PLAY_DIR):
    _abs = os.path.abspath(os.path.join(ROOT, _scratch))
    check("scratch directory %s is created inside the checkout, not beside it"
          % _scratch,
          _abs.startswith(os.path.abspath(ROOT) + os.sep), _abs)
