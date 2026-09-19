"""`--seed` actually reproduces a run: the same seed gives the same
run twice in one process, and gives the same run under a different string
hash seed too (PYTHONHASHSEED), which is what catches a float sum iterating
an unsorted set - the bug class Complaints/27 was.

Regrouped from test_round9.py - see CLAUDE.md's test-file reorganisation
note. Checks moved verbatim; the comments explain the break they guard and,
at length, why this replaced a slower and less sensitive home-grown check.
"""
from .harness import *  # noqa: F401,F403


# --- BREAK: `--seed` did not reproduce a run. Same script, same seed, three
# runs: 587,300 / 6,664,218 / 6,652,459 in capital. PYTHONHASHSEED=0 made them
# identical. Float sums over SETS: addition is not associative, the total
# gates open_venture with a hard comparison, and one bit decides a century.
def _one_run(seed=9, years=180, civ="rome_100ad"):
    run = S.Sim(NODES, ORDER, random.Random(seed), events=True, manual=False,
               civ=S.load_civ(civ), cfg={"start_capital": 100000.0})
    run.goal, run.done_year = GOAL, {}
    for _ in range(years):
        run.step()
        if run.dead_reason or run.goal_year:
            break
    return (round(run.capital, 6), len(run.done), len(run.operating),
            round(run.reputation, 9))

# THE FIRST OF THESE COSTS 190 OF THE SUITE'S SECONDS, because it simulates
# 180 years. It catches cross-instance state leaking WITHIN one process (two
# Sim objects built back to back in the same interpreter disagreeing), which
# is a different bug class from the second
# check below and one perf_fingerprint cannot see, because perf_fingerprint
# always runs its scenarios in the same order in the same process - it never
# builds two independent runs back to back the way this one does.
def _same_seed_same_run():
    first_result = _one_run()
    return _one_run() == first_result, (first_result, _one_run())

slow_check("the same seed gives the same run, twice in one process",
           _same_seed_same_run)

# THE SECOND IS NOT A NARROW, HOME-GROWN COMPARISON: comparing FOUR numbers
# (capital, len(done), len(operating), reputation) at year 180, for ONE
# civilisation and ONE seed under ONE alternate hash seed, cost 122s and
# caught its target badly. An experiment that injected a real "iterates an
# unsorted set feeding a float sum" bug (the exact class this check exists
# to catch - see ROUND 9's docstring above) measured how well each approach
# actually detects it:
#
#   the narrow four-number comparison (180 years, 1 civ, 1 seed): diverged
#       at year 107, 121 or 196 depending which seed was tried, and did not
#       diverge at ALL within 200 years for 3 of 6 seeds tried - a coin
#       flip, for the one thing it exists to catch.
#   sim/perf_fingerprint.py's state_of()/digest() (nine scenarios,
#       five civilisations, hashing the FULL save-file state every year):
#       diverged within 1-7 years on ALL NINE scenarios, every time.
#
# So the expensive, narrow, home-grown comparison is worse at its one job
# than a tool that already lives in this directory. Rebuilt on top of that
# tool instead of copying its logic (two copies of a hashing function drift
# apart and silently disagree - see perf_fingerprint.py's own comment on
# why FIELDS is derived from SAVE_FIELDS rather than hand-maintained here).
#
# Two subprocesses, not one compared against this (the parent) process:
# PYTHONHASHSEED can only be fixed at interpreter start-up, and comparing
# against whatever hash seed the parent test run happened to boot with
# made the old check's sensitivity depend on luck neither run controlled.
# Two explicit, different seeds make it the same every time this suite runs.
#
# 40 years, not perf_fingerprint's own 200-400: detection above was within
# 1-7 years on every scenario, so 40 is nearly 6x the slowest of those - a
# short horizon is not a weaker test here, it is simply not paying for 160+
# extra years of a signal that, per that measurement, is essentially always
# already in by year 7.
_HASH_SEED_HORIZON = 40


def _fingerprint_under_seed(hash_seed, years_cap):
    """Run every perf_fingerprint scenario, capped to `years_cap` years, in a
    fresh subprocess under PYTHONHASHSEED=<hash_seed>. Returns, for each
    scenario, its name and its list of per-year digests - perf_fingerprint's
    own state_of()/digest(), imported and called inside the subprocess
    (that is the only place a hash-seed change can take effect), never
    reimplemented here.
    """
    script = (
        "import json, sys\n"
        "sys.path.insert(0, %r)\n"
        "import perf_fingerprint as F\n"
        "out = []\n"
        "for sc in F.SCENARIOS:\n"
        "    nm = F.name_of(sc)\n"
        "    sc = dict(sc, years=min(sc['years'], %d))\n"
        "    s = F.build(sc)\n"
        "    digs = []\n"
        "    for _ in range(sc['years']):\n"
        "        if getattr(s, 'dead_reason', None):\n"
        "            break\n"
        "        s.step()\n"
        "        digs.append(F.digest(F.state_of(s)))\n"
        "    out.append([nm, digs])\n"
        "print(json.dumps(out))\n"
    ) % (HERE, years_cap)
    det = subprocess.run([sys.executable, "-c", script], capture_output=True,
                         text=True, timeout=600,
                         env=dict(os.environ, PYTHONHASHSEED=str(hash_seed)))
    if det.returncode != 0:
        raise RuntimeError("fingerprint subprocess (hash seed %s) failed: %s"
                           % (hash_seed, det.stderr[-2000:]))
    return json.loads(det.stdout)


def _same_under_other_hash_seed():
    fingerprints_a = _fingerprint_under_seed(0, _HASH_SEED_HORIZON)
    fingerprints_b = _fingerprint_under_seed(1234567, _HASH_SEED_HORIZON)
    if fingerprints_a == fingerprints_b:
        return True, ""
    for (scenario_name, digests_a), (_, digests_b) in zip(fingerprints_a, fingerprints_b):
        if digests_a != digests_b:
            diverged_at_year = next((year for year in range(min(len(digests_a), len(digests_b)))
                      if digests_a[year] != digests_b[year]), min(len(digests_a), len(digests_b)))
            return False, "%s diverged at year %d" % (scenario_name, diverged_at_year)
    return False, "run lengths differ: %r vs %r" % (
        [len(digests) for _, digests in fingerprints_a], [len(digests) for _, digests in fingerprints_b])


slow_check("...and the same run in a process with a different string hash seed",
           _same_under_other_hash_seed)
