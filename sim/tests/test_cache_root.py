"""The on-disk caches have one home: the main checkout's `.cache/`, shared by every git worktree of it, or
the directory ROME_CACHE_DIR names. Cache keys hash content with paths relative to the checkout, so a
shared cache only ever answers with what this checkout would compute.

sim/cache_root.py."""
QUICK_TOPIC = True

import os
import re
import tempfile
import unittest
from unittest import mock

from sim import cache_root

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class CacheRootTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.mkdtemp(prefix="cache_root_")
        self.environment = mock.patch.dict(os.environ, {}, clear=False)
        self.environment.start()
        os.environ.pop(cache_root.CACHE_DIRECTORY_ENV, None)

    def tearDown(self):
        self.environment.stop()

    def test_a_plain_checkout_keeps_its_own_cache(self):
        checkout = os.path.join(self.directory, "checkout")
        os.makedirs(os.path.join(checkout, ".git"))
        self.assertEqual(cache_root.cache_root(checkout), os.path.join(checkout, ".cache"))

    def test_a_copy_with_no_git_keeps_its_own_cache(self):
        self.assertEqual(cache_root.cache_root(self.directory), os.path.join(self.directory, ".cache"))

    def test_a_worktree_shares_the_main_checkouts_cache(self):
        main = os.path.join(self.directory, "main")
        worktree_record = os.path.join(main, ".git", "worktrees", "feature")
        _write(os.path.join(worktree_record, "commondir"), "../..\n")
        worktree = os.path.join(self.directory, "elsewhere", "feature")
        _write(os.path.join(worktree, ".git"), "gitdir: %s\n" % worktree_record)
        self.assertEqual(cache_root.cache_root(worktree), os.path.join(main, ".cache"))

    def test_a_relative_gitdir_is_read_from_the_worktree(self):
        main = os.path.join(self.directory, "main")
        _write(os.path.join(main, ".git", "worktrees", "feature", "commondir"), "../..\n")
        worktree = os.path.join(main, "trees", "feature")
        _write(os.path.join(worktree, ".git"), "gitdir: ../../.git/worktrees/feature\n")
        self.assertEqual(cache_root.cache_root(worktree), os.path.join(main, ".cache"))

    def test_an_unreadable_worktree_record_falls_back_to_the_checkout(self):
        worktree = os.path.join(self.directory, "broken")
        _write(os.path.join(worktree, ".git"), "gitdir: %s\n" % os.path.join(self.directory, "missing"))
        self.assertEqual(cache_root.cache_root(worktree), os.path.join(worktree, ".cache"))

    def test_the_environment_names_a_cache_for_separate_clones(self):
        shared = os.path.join(self.directory, "shared")
        os.environ[cache_root.CACHE_DIRECTORY_ENV] = shared
        self.assertEqual(cache_root.cache_root(self.directory), shared)


class OneHomeTests(unittest.TestCase):
    def test_no_other_module_builds_a_cache_path_of_its_own(self):
        pattern = re.compile(r"""["']\.cache["']""")
        offenders = []
        for directory, subdirectories, filenames in os.walk(os.path.join(ROOT, "sim")):
            subdirectories[:] = [name for name in subdirectories if name not in ("tests", "__pycache__")]
            for filename in filenames:
                path = os.path.join(directory, filename)
                if filename.endswith(".py") and path != cache_root.__file__.replace(".pyc", ".py"):
                    with open(path, encoding="utf-8") as handle:
                        if pattern.search(handle.read()):
                            offenders.append(os.path.relpath(path, ROOT))
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
