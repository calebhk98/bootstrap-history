# Nothing a player does before an attempt lowers its failure risk

**Status:** closed - nodes declare a `precaution` mechanic (a pilot plant or a redundant team: a share of the bill and of the founder's hours added); `start ... precaution` pays it through the ordinary bill and hours, `effective_risk` divides the chance by the relief bought (a labelled heuristic, `RELIEF_PER_COST_SHARE`), and `why` quotes cost and chance with and without (`pay_to_lower_the_risk`). Regression: `sim/tests/test_risk_precaution.py`. Declared on every node whose risk and calendar floor are both high (find them with the data script in the commit); a pilot plant as its own optional input node was not built.

**Source:** `reports/TOP_PROBLEMS.md` items 2 and 4 (long calendar floors with unmitigable failure rolls). The platinum placeholder risk in item 4 was fixed separately; the general problem was not.

## What is wrong

A project's failure chance is its node `risk`, lowered only by having already
failed (the retry multiplier). Once the money, staff, materials and science
are all in place there is nothing left to improve before the dice roll, so a
mandatory multi-year project can cost several years per failed roll with no
strategic response. The report's late game was decided by these rolls, not by
choices.

## Evidence

- `sim/engine/projects_progress.py`, `effective_risk` - the node's `risk` times
  the retry multiplier times `_control_relief_multiplier`, which only a completed
  process controller moves, and only for process-control nodes.
- `python3 sim/simulator.py why <node>` prints "Failure risk: N% per attempt"
  with no way to buy it down. Finding the exposed nodes means scanning
  `data/tech_tree.json` for high `risk` together with a long `yrs`; no
  committed command does this yet.

## Why it matters

Uncertainty is good; uncertainty with no lever turns a calendar floor into a
lottery. The fix must not make every project safe, or the risk display and
the retry learning curve stop meaning anything.

## What it would take

A physical lever, not a flat discount: pilot plant or prototype work as its
own node that the risky project lists as an optional input, redundant teams
running the attempt in parallel (more hours and staff for a lower chance), or
quality-control spend. It must go through the normal cost and staff rules
(`CLAUDE.md` section 4.3) and be data-driven per node (`failure_kind` already
exists on some nodes). Regression test: the same node quoted with and without
the lever differs in risk and in cost.

Checked against current code: `effective_risk` reads one extra input beyond retry learning, the process-controller relief; no pilot-plant, redundancy or quality-control lever exists for other nodes.
