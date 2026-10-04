"""Shared set-up for tests that run the suite from a throwaway checkout of symlinks."""
import os


def link_build_caches(root, alias_root):
    """Point alias_root/.cache's build caches at root's, so the throwaway checkout does not rebuild
    the tree, price solves and spin-up from cold. The runner's timing file stays separate."""
    source = os.path.join(root, ".cache")
    target = os.path.join(alias_root, ".cache")
    os.makedirs(target, exist_ok=True)
    if os.path.isdir(source):
        for entry in os.listdir(source):
            if os.path.isdir(os.path.join(source, entry)):
                os.symlink(os.path.join(source, entry), os.path.join(target, entry))
