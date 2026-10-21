"""Complaint 620: what a state collects on a tile follows from the officials it employs, their literacy and the road
from its seat, not from a typed state capacity."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim

from sim.engine.agents_port import SimWorld
from sim.agents import budget, collection, revenue

WORKING_DAYS = 200.0
PEOPLE = {"seat": 10_000.0, "near": 10_000.0, "far": 10_000.0}
DAYS = {"seat": 0.0, "near": 2.0, "far": 40.0}
SCARCE_OFFICIALS = 3.0   # 600 official-days against 600 and more asked


def weighted(officials, literacy=0.0, days=DAYS):
    shares = collection.tile_shares(officials, WORKING_DAYS, literacy, PEOPLE, days)
    return shares, collection.collectible_share(shares, PEOPLE)


# ---- the officials and their time ----------------------------------------------------------------
shares_few, total_few = weighted(SCARCE_OFFICIALS)
shares_double, total_double = weighted(2.0 * SCARCE_OFFICIALS)
check("with officials short of the work, doubling them raises what is collected", total_double > total_few, (total_few, total_double))
check("every tile gains from the extra officials, none loses",
      all(shares_double[tile] >= shares_few[tile] for tile in PEOPLE), (shares_few, shares_double))
check("a share is never more than all of what is due", max(shares_double.values()) <= 1.0)
check("no officials collect nothing", weighted(0.0)[1] == 0.0)
_all_reach, total_many = weighted(1.0e6)
check("officials enough for the work collect all of it", abs(total_many - 1.0) < 1e-12, total_many)

# ---- the road ---------------------------------------------------------------------------------------
check("a far tile yields a smaller share than a near one of the same people",
      shares_few["far"] < shares_few["near"] <= shares_few["seat"], shares_few)
check("a tile with no road from the seat yields nothing",
      weighted(SCARCE_OFFICIALS, days={"seat": 0.0, "near": 2.0})[0]["far"] == 0.0)
slower = dict(DAYS, near=20.0)
check("lengthening the road to a tile lowers its share",
      weighted(SCARCE_OFFICIALS, days=slower)[0]["near"] < shares_few["near"])
check("the seat is the tile with the most people", collection.seat_tile({"a": 1.0, "b": 5.0, "c": 5.0}) == "b")

# ---- writing ---------------------------------------------------------------------------------------
check("literate officials collect more than unlettered ones with the same time",
      weighted(SCARCE_OFFICIALS, literacy=1.0)[1] > total_few, (total_few, weighted(SCARCE_OFFICIALS, literacy=1.0)[1]))

# ---- unpaid officials do not collect ---------------------------------------------------------------------
check("officials left unpaid are not employed",
      collection.officials_employed(100.0, 1000.0, 250.0) == 75.0 and collection.officials_employed(100.0, 0.0, 0.0) == 100.0)

# ---- the world: the shares come from officials and the road, and no typed capacity is read -------------------------------
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
