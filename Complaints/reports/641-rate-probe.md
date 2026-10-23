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

## Probe 3: what `market_rate()` reads, clearing by clearing (2026-10-22)

Run from a checkout root with `ROME_CACHE_DIR` set to an empty directory (the cached spin-up would skip the clearings), once per
civilisation: `ROME_CACHE_DIR=<empty dir> python3 -W ignore probe3.py england_1300`.

```python
import sys, statistics
sys.path.insert(0, ".")
from sim.economy import credit, economy as eco
events = []
orig = credit.clear_with_cause
def spy(requests, offers, currency, last_rate, *a, **k):
    r = orig(requests, offers, currency, last_rate, *a, **k)
    rq = [x for x in requests if x.amount > 0 and x.currency == currency]
    of = [o for o in offers if o.amount > 0 and o.currency == currency]
    asks = sorted(o.minimum_rate for o in of)
    # ask of the marginal lender: funds at or below base
    at_rate = sum(o.amount for o in of if r.rate is not None and o.minimum_rate <= r.rate)
    events.append("CLEAR year=%s reqs=%d asked=%.3g offers=%d funds=%.3g asks(min/med/max)=%s last=%s rate=%s cause=%s lent=%.3g funds_at_rate=%.3g mean_loan_rate=%s" % (
        k.get("year"), len(rq), sum(x.amount for x in rq), len(of), sum(o.amount for o in of),
        tuple(round(v,4) for v in (asks[0], statistics.median(asks), asks[-1])) if asks else None,
        None if last_rate is None else round(last_rate,4), r.rate, r.cause, sum(l.principal for l in r.loans), at_rate,
        round(sum(l.rate*l.principal for l in r.loans)/sum(l.principal for l in r.loans),4) if r.loans else None))
    return r
credit.clear_with_cause = spy
os = eco.labour.sticky_move
def sm(cur, tgt, share):
    r = os(cur, tgt, share); events.append("NO_REQUESTS_DRIFT cur=%s floor=%s -> %.4f" % (cur, tgt, r)); return r
eco.labour.sticky_move = sm
from sim.tests.harness import sim
g = sim(civ=sys.argv[1])
print(sys.argv[1], "market_rate", g.market_rate(), "starting", g.civ["starting_interest_rate"])
for e in events: print(e)
```

The last clearing line of the output is the year's second clearing, the one whose rate memory keeps. At the opening, before the
change: england_1300 0.0043, rome_100ad 0.0255, han_china_100ad 0.122. After: england_1300 0.0 (asks 0.0 to 0.07, median 0.0014;
funds at the rate exceed the request), rome_100ad 0.031 (asks 0.0 to 0.36, median 0.147; mean loan rate 0.115 with premiums),
han_china_100ad 0.138 (asks 0.13 to 0.48, median 0.147; mean loan rate 0.24). Each rate is at or above the lowest ask, and the
lenders asking no more than it hold at least what was lent.
