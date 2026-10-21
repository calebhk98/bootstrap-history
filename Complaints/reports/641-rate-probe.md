# Complaint 641: why the opening rate sits at the lenders' ceiling (probe)

Measured 2026-10-21 on main 3cb9c9a0 in a checkout pinned to that commit, from its root: `python3 <probe>.py`, where the probe
is one of the two scripts below. The figures are this measurement's output; re-run the scripts for current ones.

## Probe 1: wrap `credit.clear` and step one year

```python
"""Capture the credit clearing of one stepped year in an opened Rome game (full spin-up)."""
import os, sys, statistics
sys.path.insert(0, os.getcwd())
from sim.tests import harness
os.environ.pop("ROME_SPIN_UP_YEARS", None)
from sim.economy import credit
calls = []
original = credit.clear
def spy(requests, offers, currency, last_rate, *args, **kwargs):
    result = original(requests, offers, currency, last_rate, *args, **kwargs)
    unclamped = original(requests, offers, currency, last_rate, *args, **dict(kwargs, rate_ceiling=None))
    calls.append((list(requests), list(offers), last_rate, kwargs.get("rate_ceiling"), result, unclamped))
    return result
credit.clear = spy
game = harness.sim(capital=1e7)
print("built; calls during build:", len(calls))
calls.clear()
game.step() if hasattr(game, "step") else None
print("calls during one step:", len(calls))
for requests, offers, last_rate, ceiling, (loans, rate, unmet), (_l2, free_rate, _u2) in calls:
    asked = sum(r.amount for r in requests); funds = sum(o.amount for o in offers)
    caps = sorted(r.maximum_rate for r in requests if r.amount > 0)
    asks = sorted(o.minimum_rate for o in offers if o.amount > 0)
    by_purpose = {}
    for r in requests:
        by_purpose.setdefault(getattr(r, "purpose", "?"), [0.0, 0])
        by_purpose[getattr(r, "purpose", "?")][0] += r.amount; by_purpose[getattr(r, "purpose", "?")][1] += 1
    print("last_rate %.3f ceiling %s rate %.3f unclamped %.3f | asked %.3g funds %.3g lent %.3g unmet %.3g" % (
        last_rate or 0, ceiling, rate, free_rate, asked, funds, sum(l.amount for l in loans), sum(u.amount for u in unmet)))
    if caps: print("  borrower caps: n %d min %.3f median %.3f max %.3f" % (len(caps), caps[0], statistics.median(caps), caps[-1]))
    if asks: print("  lender asks:   n %d min %.3f median %.3f max %.3f" % (len(asks), asks[0], statistics.median(asks), asks[-1]))
    print("  requests by purpose:", {k: ("%.3g" % v[0], v[1]) for k, v in by_purpose.items()})
```

Output:

```
built; calls during build: 0
calls during one step: 2
last_rate 0.480 ceiling 0.48 rate 0.480 unclamped 0.638 | asked 3.49e+09 funds 3.89e+10 lent 0 unmet 3.49e+09
  borrower caps: n 535 min 0.002 median 2.018 max 1990030.599
  lender asks:   n 278 min 0.638 median 0.644 max 1.049
  requests by purpose: {'working capital': ('3.49e+09', 535)}
last_rate 0.480 ceiling 0.48 rate 0.480 unclamped 0.650 | asked 2.2e+09 funds 1.21e+09 lent 0 unmet 2.2e+09
  borrower caps: n 585 min 0.250 median 0.480 max 32209.812
  lender asks:   n 4 min 0.650 median 0.930 max 1.049
  requests by purpose: {'expand': ('1.65e+05', 83), 'enter': ('1.06e+07', 225), 'credit line': ('3.3e+04', 1), 'subsistence': ('1.73e+09', 260), 'trade': ('4.61e+08', 16)}
```

## Probe 2: the parts of the lenders' ask at the opening

```python
import os, sys, statistics
sys.path.insert(0, os.getcwd())
from sim.tests import harness
os.environ.pop("ROME_SPIN_UP_YEARS", None)
from sim.economy import households_orders
from sim.economy.lending import capital_market
game = harness.sim(capital=1e7)
economy = game.economy._answering_agent().economy()
record, setup = economy.record, economy.setup
inflation = [c.expected_inflation for c in record.cohorts.values()]
losses = [record.loss_rates.get(cid, 0.0) for cid in record.cohorts]
print("opening_rate", setup.opening_rate, "ceiling share", capital_market.RATE_CEILING_SHARE, "time preference", households_orders.HOUSEHOLD_TIME_PREFERENCE)
print("expected inflation: min %.3f median %.3f max %.3f" % (min(inflation), statistics.median(inflation), max(inflation)))
print("cohort loss rates: min %.3f median %.3f max %.3f; nonzero %d of %d" % (min(losses), statistics.median(losses), max(losses), sum(1 for x in losses if x > 0), len(losses)))
print("all loss_rates keys sample", list(record.loss_rates.items())[:5])
levels = getattr(record.memory, "price_levels", None) or getattr(record.memory, "price_level", None)
print("price level memory:", levels if not isinstance(levels, dict) else list(levels.items())[-6:])
```

Output:

```
opening_rate 0.12 ceiling share 4.0 time preference 0.05
expected inflation: min 0.588 median 0.588 max 0.588
cohort loss rates: min 0.000 median 0.004 max 0.411; nonzero 312 of 312
```

Reading: the ask is time preference plus expected inflation (plus a small loss rate for most cohorts), above the ceiling for
every lender, so nothing is lent although funds exceed requests in the first clearing.
