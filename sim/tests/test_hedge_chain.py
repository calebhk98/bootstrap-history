"""hedge_chain: the calendar floor of a hedge is what its chain still needs, so a player partway through sees what is left.

The strongest hedge against being sacked (the copies of your work kept somewhere else) sits behind a long chain; its floor
comes from the tree and from what is done. The lead time the advice states is in test_hedge_lead_time."""
from .harness import *  # noqa: F401,F403

from sim.engine.data import critical_path
from sim.engine.hazard_hedge_timing import remaining_floor_years

QUICK_TOPIC = True

STRONGEST_HEDGE = "academy_network"
_total, CHAIN = critical_path(NODES, STRONGEST_HEDGE)
STANDING_START = remaining_floor_years(NODES, CHAIN, set())

check("the strongest sack_chance hedge has a calendar floor of decades from a standing start (the chain two playtesters "
      "met), not years", 20.0 <= STANDING_START <= 30.0, STANDING_START)

PARTLY_DONE = {"scientific_method", "corpus_written"}
partial = remaining_floor_years(NODES, CHAIN, PARTLY_DONE)
check("once part of the chain is done the floor is smaller by exactly those nodes' own years",
      abs(partial - (STANDING_START - NODES["scientific_method"]["yrs"] - NODES["corpus_written"]["yrs"])) < 1e-6,
      (partial, STANDING_START))
check("...and once all of it is done nothing is left to wait for", remaining_floor_years(NODES, CHAIN, set(CHAIN)) == 0.0)

toy = {"a": {"yrs": 3.0, "ph": 0.0}, "b": {"yrs": 1.0, "ph": 8000.0}, "c": {"yrs": 2.0, "ph": 100.0}}
check("each node counts for the longer of its years and its work at a lone worker's pace",
      remaining_floor_years(toy, ["a", "b", "c"], set()) == 3.0 + 4.0 + 2.0, remaining_floor_years(toy, ["a", "b", "c"], set()))
check("a node already done is left out", remaining_floor_years(toy, ["a", "b", "c"], {"b"}) == 5.0)
check("a chain with nothing in it needs no time", remaining_floor_years(toy, [], set()) == 0.0)
