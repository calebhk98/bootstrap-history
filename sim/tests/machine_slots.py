"""Machine-wide worker slots for the suite. Every suite run on the machine draws its parallel workers from
one pool with a slot per core, so several suites at once (agents in worktrees) queue for cores instead
of overcommitting them and the memory. A slot is an exclusive lock on a file, so a holder that dies
frees it."""
import os
import tempfile
import time

try:
    import fcntl
except ImportError:  # Windows: no shared pool, each suite keeps its own --jobs
    fcntl = None

SLOTS_DIRECTORY_ENV = "ROME_SUITE_SLOTS_DIR"
WAIT_BETWEEN_TRIES_SECONDS = 0.2


def slots_directory():
    return os.environ.get(SLOTS_DIRECTORY_ENV) or os.path.join(tempfile.gettempdir(), "rome_suite_slots")


def slot_count():
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def acquire(count=None, directory=None, wait=True):
    """An open handle holding one free slot, or None where slots are unavailable. With `wait` it waits
    until a slot frees; without, it returns False when none is free (a caller still holding slots must
    reap its own workers rather than wait, or two suites could each wait on the other's)."""
    if fcntl is None:
        return None
    directory = directory or slots_directory()
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return None
    count = count or slot_count()
    while True:
        for number in range(count):
            try:
                handle = open(os.path.join(directory, "slot_%d.lock" % number), "a")  # noqa: SIM115 - held open as the slot
            except OSError:
                return None
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return handle
            except OSError:
                handle.close()
        if not wait:
            return False
        time.sleep(WAIT_BETWEEN_TRIES_SECONDS)


def release(handle):
    if handle is not None:
        handle.close()
