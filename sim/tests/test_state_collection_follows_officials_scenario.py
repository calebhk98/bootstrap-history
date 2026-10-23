"""SCENARIO (Complaint 620): in the home game the collectible share and the assessment come from the officials kept and paid, never
from a typed capacity; unpaid officials collect less. The share arithmetic is in test_state_collection_follows_officials."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim

from sim.engine.agents_port import SimWorld
from sim.agents import budget, revenue

game = sim(civ="rome_100ad")
game.civ["state_revenue"] = [{"form": "poll_tax", "basis": "adult_labour_years", "rate": 0.02}]


class CapacityRead(Exception):
    pass


def refuse():
    raise CapacityRead("the state reach was read")


world = SimWorld(game)
world.state_reach = refuse   # any read of the state reach during collection fails the check
read_typed = False
try:
    kept = budget.officials_kept(world)
    full = world.collectible_share()
    assessed = revenue.assess(world)
except CapacityRead:
    read_typed = True
check("neither the officials kept, the collectible share nor the assessment read the state reach", not read_typed)
check("the state keeps officials from its people alone", abs(kept - world.population_total() / budget.ADMINISTRATIVE_SPAN) < 1e-9, kept)
check("an assessment records the share it reached", all(0.0 <= each.collectible <= 1.0 for each in assessed), assessed)

check("no civilisation file carries a typed state capacity", "state_capacity" not in game.civ, sorted(game.civ))

record = SimWorld(game).government().record
need = budget.officials_kept(world) * world.pay_per_person_year("scribe")
record.unfunded = {"administration": 0.999 * need}
starved = SimWorld(game)
check("when the officials' pay goes unmet, the state employs fewer and collects less",
      starved.officials_employed() < 0.01 * kept + 1e-9 and starved.collectible_share() < full,
      (starved.officials_employed(), kept, starved.collectible_share(), full))
check("what the state collects falls with its collectible share",
      sum(each.money for each in revenue.assess(starved)) < sum(each.money for each in assessed))
