"""Regression coverage for Complaints/38: `cli.py` used to print one founder
lifetime-hours budget and judge feasibility against a different one.

Not registered in sim/tests/__main__.py's TOPICS list yet - out of scope for
the agent that wrote this file (cli.py/data.py and test files only). Needs
"complaint_38_founder_lifetime" added there for `test_regressions.py` to run
it as part of the full suite.
"""
import argparse
import contextlib
import io
import re

from .harness import *  # noqa: F401,F403
import sim.engine.cli as ENGINE_CLI


def _run_cmd_path(goal=None):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        S.cmd_path(argparse.Namespace(goal=goal))
    return buf.getvalue()


def _run_cmd_why(node_id):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        S.cmd_why(argparse.Namespace(node=node_id, goal=None))
    return buf.getvalue()


_AVAILABLE_LINE = re.compile(
    r"Founder-hours available in one lifetime at ([\d,]+)/yr for ([\d,]+) yrs: ([\d,]+)")
_DEMANDED_LINE = re.compile(
    r"Founder-hours demanded by this path\s*:\s*([\d,]+)")
_WHY_HOURS_LINE = re.compile(
    r"Your hours\s+:\s*([\d,.]+)\s+\(([\d.]+)% of a ([\d,]+)-hour life\)")


def _int(token):
    return int(float(token.replace(",", "")))


def _parse_path_output(output):
    hours_per_year, working_years, available = _AVAILABLE_LINE.search(output).groups()
    demanded, = _DEMANDED_LINE.search(output).groups()
    feasible = "feasible alone in principle" in output
    impossible = "IMPOSSIBLE for one person" in output
    assert feasible != impossible, "cmd_path printed neither or both verdicts:\n" + output
    return {
        "hours_per_year": _int(hours_per_year),
        "working_years": _int(working_years),
        "available": _int(available),
        "demanded": _int(demanded),
        "feasible": feasible,
    }


# --- 1. Under today's real DEFAULTS, the printed budget and the judged
# budget must be the SAME number, and that number must itself equal
# hours/year * working years, not an independently-typed figure that
# happens to match today.
_parsed_default = _parse_path_output(_run_cmd_path())
_expected_default = S.DEFAULTS["founder_hours_per_year"] * S.DEFAULTS["founder_life_mean"]
check("cmd_path's printed lifetime-hours figure equals hours/yr * working years "
      "read from DEFAULTS",
      _parsed_default["available"] == _expected_default, _parsed_default)
check("cmd_path's printed per-year and per-life figures ARE DEFAULTS' own "
      "founder_hours_per_year and founder_life_mean, not separate literals",
      _parsed_default["hours_per_year"] == S.DEFAULTS["founder_hours_per_year"]
      and _parsed_default["working_years"] == S.DEFAULTS["founder_life_mean"],
      _parsed_default)
check("cmd_path's feasibility verdict agrees with its own printed numbers",
      _parsed_default["feasible"] == (_parsed_default["demanded"] < _parsed_default["available"]),
      _parsed_default)

# --- 2. THE REAL TEST: prove the two numbers cannot merely be "currently
# equal" typed literals, by moving DEFAULTS and checking BOTH the printed
# budget and the verdict move with it - to a value neither of the old two
# separately-typed literals (72,000, or the complaint's "corrected" 60,000)
# would ever produce. The old bug always judged this exact goal's path as
# feasible (its demand, ~53,830h, was under BOTH old literals); a fix that
# only reads DEFAULTS should say IMPOSSIBLE once DEFAULTS makes the true
# budget smaller than the demand, and should print that smaller number too.
_original_hours_per_year = S.DEFAULTS["founder_hours_per_year"]
_original_life_mean = S.DEFAULTS["founder_life_mean"]
try:
    S.DEFAULTS["founder_hours_per_year"] = 500
    S.DEFAULTS["founder_life_mean"] = 10
    _parsed_shrunk = _parse_path_output(_run_cmd_path())
finally:
    S.DEFAULTS["founder_hours_per_year"] = _original_hours_per_year
    S.DEFAULTS["founder_life_mean"] = _original_life_mean

check("shrinking DEFAULTS' founder hours/year and working years moves the "
      "PRINTED budget to their product (5,000), not a leftover literal",
      _parsed_shrunk["available"] == 5000
      and _parsed_shrunk["hours_per_year"] == 500
      and _parsed_shrunk["working_years"] == 10,
      _parsed_shrunk)
check("...and the JUDGEMENT flips to IMPOSSIBLE with it, proving the verdict "
      "reads the same shrunk number rather than a separate 72,000/60,000 "
      "constant that neither old literal would ever have flipped on this path",
      not _parsed_shrunk["feasible"] and _parsed_shrunk["demanded"] > 5000,
      _parsed_shrunk)

# --- 3. cmd_why's "% of a life" figure is the SAME lifetime-hours number
# cmd_path uses, under the same (shrunk) DEFAULTS - not a third, independent
# 72,000 (the old literal cmd_why used to read).
_node_id = "point_contact_transistor"
try:
    S.DEFAULTS["founder_hours_per_year"] = 500
    S.DEFAULTS["founder_life_mean"] = 10
    _why_output = _run_cmd_why(_node_id)
finally:
    S.DEFAULTS["founder_hours_per_year"] = _original_hours_per_year
    S.DEFAULTS["founder_life_mean"] = _original_life_mean
_why_hours, _why_pct, _why_life = _WHY_HOURS_LINE.search(_why_output).groups()
check("cmd_why's printed 'hour life' denominator is the same shrunk 5,000 "
      "cmd_path would print under the same DEFAULTS",
      _int(_why_life) == 5000, _why_output)
check("cmd_why's percentage is exactly node hours / that same lifetime figure",
      abs(float(_why_pct) - 100.0 * _int(_why_hours) / 5000.0) < 0.05,
      (_why_hours, _why_pct, _why_life))


# --- 4. Complaints/38 section 2: the mortality sweep's own founder-lifespan
# standard deviation must be DEFAULTS['founder_life_sd'] (8.0), the same
# figure core.py's real mortality draw and this file's own _ingame_options
# use - not a separate, half-sized 4.0 baked into the sweep.
class _RecordingSim(ENGINE_CLI.Sim):
    captured_cfgs = []

    def __init__(self, *args, **kwargs):
        _RecordingSim.captured_cfgs.append(dict(kwargs.get("cfg") or {}))
        super().__init__(*args, **kwargs)


_original_sim_cls = ENGINE_CLI.Sim
ENGINE_CLI.Sim = _RecordingSim
try:
    with contextlib.redirect_stdout(io.StringIO()):
        S.cmd_sweep(argparse.Namespace(
            axis="mortality", strategy="recommended", goal=None,
            mc=1, seed=1, horizon=10))
finally:
    ENGINE_CLI.Sim = _original_sim_cls

_mortality_cfgs = [cfg for cfg in _RecordingSim.captured_cfgs if "founder_life_mean" in cfg]
check("cmd_sweep's mortality axis actually constructed Sims to inspect",
      len(_mortality_cfgs) >= 6, len(_mortality_cfgs))
check("cmd_sweep's mortality axis draws founder lifespan at "
      "DEFAULTS['founder_life_sd'] (8.0), the same spread every real game "
      "uses - not a separate, half-sized 4.0",
      all(cfg.get("founder_life_sd") == S.DEFAULTS["founder_life_sd"]
          for cfg in _mortality_cfgs),
      _mortality_cfgs)
