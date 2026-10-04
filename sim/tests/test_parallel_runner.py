"""The parallel topic runner prints exactly what a sequential run prints."""
import re
import shutil
import tempfile

from .harness import *
from .alias_checkout import link_build_caches

# A throwaway checkout whose sim/ and sim/tests/ are symlink farms, so extra
# fake topics can sit beside real ones without touching this checkout.
_alias_root = tempfile.mkdtemp(prefix="parallel_runner_")


def _link_entries(source_dir, target_dir, skip=()):
    os.makedirs(target_dir, exist_ok=True)
    for entry in os.listdir(source_dir):
        if entry in skip or entry == "__pycache__":
            continue
        os.symlink(os.path.join(source_dir, entry), os.path.join(target_dir, entry))


def _run_suite(*args):
    completed = subprocess.run(
        [sys.executable, os.path.join(_alias_root, "sim", "tests", "__main__.py")] + list(args),
        capture_output=True, text=True, timeout=600, cwd=_alias_root)
    return completed


def _without_timing(text):
    # Per-check timings and the summary's total seconds vary run to run.
    text = re.sub(r"^slowest:\n(?:[ ]+\d+s .*\n)*", "", text, flags=re.MULTILINE)   # which checks ran slow depends on cache warmth
    text = re.sub(r"[ ]+\d+s$", "", text, flags=re.MULTILINE)
    text = re.sub(r"(\d+ failures), \d+s", r"\1", text)
    return re.sub(r"\d+ calls, \d+s waiting", "N calls, Ns waiting", text)


try:
    for entry in ("data", "docs", "mods", "playtest", "Complaints"):
        if os.path.exists(os.path.join(ROOT, entry)):
            os.symlink(os.path.join(ROOT, entry), os.path.join(_alias_root, entry))
    link_build_caches(ROOT, _alias_root)
    _link_entries(os.path.join(ROOT, "sim"), os.path.join(_alias_root, "sim"), skip=("tests",))
    _link_entries(os.path.join(ROOT, "sim", "tests"), os.path.join(_alias_root, "sim", "tests"),
                  skip=("test_parallel_runner.py",))
    _fake_dir = os.path.join(_alias_root, "sim", "tests")
    with open(os.path.join(_fake_dir, "test_zz_fake_fail.py"), "w") as handle:
        handle.write("from .harness import *\n"
                     "check('fake topic passing check', True)\n"
                     "check('fake topic failing check', False, 'because')\n")
    with open(os.path.join(_fake_dir, "test_zz_fake_crash.py"), "w") as handle:
        handle.write("raise RuntimeError('boom at import')\n")

    _topics = "agriculture,market_clearing,mod_overrides"
    _sequential = _run_suite("--only", _topics, "--jobs", "1")
    _parallel = _run_suite("--only", _topics, "--jobs", "4")
    check("parallel run of a topic set prints the same content and order as --jobs 1",
          _without_timing(_sequential.stdout) == _without_timing(_parallel.stdout)
          and " 0 checks," not in _sequential.stdout,
          (_sequential.stdout[-300:], _parallel.stdout[-300:], _parallel.stderr[-300:]))
    check("...and both exit zero",
          _sequential.returncode == 0 and _parallel.returncode == 0,
          (_sequential.returncode, _parallel.returncode, _sequential.stdout[-500:], _sequential.stderr[-500:]))

    _failing = _run_suite("--only", "agriculture,zz_fake_fail,mod_overrides", "--jobs", "4")
    _failing_sequential = _run_suite("--only", "agriculture,zz_fake_fail,mod_overrides",
                                     "--jobs", "1")
    check("a failing check in one parallel topic is reported by name, in order, with exit 1",
          _failing.returncode == 1
          and "FAILED: fake topic failing check because" in _failing.stdout
          and _without_timing(_failing.stdout) == _without_timing(_failing_sequential.stdout),
          (_failing.returncode, _failing.stdout[-400:]))

    _crashing = _run_suite("--only", "agriculture,zz_fake_crash", "--jobs", "4")
    check("a topic that crashes on import is reported as a failure naming it, exit 1",
          _crashing.returncode == 1 and "zz_fake_crash: worker crashed" in _crashing.stdout
          and "boom at import" in _crashing.stdout,
          (_crashing.returncode, _crashing.stdout[-400:]))

    _listing = _run_suite("--list", "--jobs", "4")
    check("--list is unaffected by --jobs",
          _listing.returncode == 0 and "zz_fake_fail" in _listing.stdout.split(),
          _listing.stdout[-200:])
finally:
    shutil.rmtree(_alias_root, ignore_errors=True)
