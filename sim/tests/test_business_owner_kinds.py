"""One business, run by a firm, a player and a state, has the same crew, upkeep, takings and books.

Stage 1 of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md: what differs between owners is who decides, never the arithmetic."""

QUICK_TOPIC = True

import json

from .harness import check

from sim.agents import business_books, business_closing
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business
from sim.engine.state import _deserialize_typed, serialize_state

from .agents_fake_world import FakeWorld, make_node

OWNER_KINDS = ("firm", "player", "government")
SIZE = 2.5
OPENED = 95
OPENING_MONEY = 5000.0


def make_world():
	world = FakeWorld(year=100)
	world.nodes["shop"] = make_node("shop", hours=4000.0, revenue=20000.0, upkeep=60.0)
	world.free_people["labourer"] = 100.0
	return world


def owners_of_one_business():
	registry = ActorRegistry(ActorsState(home_country="home"))
	owners = {}
	for kind in OWNER_KINDS:
		owner = registry.add("%s:1" % kind, ActorRecord(kind=kind, money=OPENING_MONEY, founded_year=90))
		owner.business.open_plant("shop", OPENED)
		owner.business.set_size("shop", SIZE)
		owners[kind] = owner
	return owners


def one_year(owner, world):
	margin = business_books.operate(owner.business, owner, "shop", world, 1.0)
	carried = business_books.carry(owner.business, owner, "shop", world)
	return margin, carried


world = make_world()
owners = owners_of_one_business()
results = {kind: one_year(owner, world) for kind, owner in owners.items()}
check("the three owners' businesses are the same plant", len({tuple((plant.entry_key, plant.size, plant.opened_year)
	  for plant in owner.business.plants) for owner in owners.values()}) == 1)
check("the same year gives the same margin and carrying cost to a firm, a player and a state",
	  len(set(results.values())) == 1 and results["firm"][0] > 0.0, results)
check("it takes the same crew", len({tuple(sorted(owner.workforce.items())) for owner in owners.values()}) == 1
	  and owners["firm"].workforce["labourer"] == world.concern_staff("shop")["labourer"] * SIZE, owners["firm"].workforce)
check("it finds the same share of its crew", len({owner.staffed_share("shop") for owner in owners.values()}) == 1)
check("it pays the same: money after the year is the same", len({round(owner.money, 9) for owner in owners.values()}) == 1)
expected = OPENING_MONEY + world.concern_takings("shop", OPENED, 1.0, SIZE) - world.upkeep("shop", SIZE) \
	- world.concern_wage_bill("shop", SIZE) - results["firm"][1]
check("takings less upkeep, wages and carrying cost is what the purse gained", all(abs(owner.money - expected) < 1e-6 for owner in owners.values()),
	  [owner.money for owner in owners.values()])
check("the books balance per owner: purse = opening + income - outlays",
	  all(abs(owner.money - (OPENING_MONEY + sum(owner.record.income.values()) - sum(owner.record.outlays.values()))) < 1e-6
		  for owner in owners.values()))

# ---- a crew the pool cannot supply makes less, for every owner alike ----------------------------------
world.free_people["labourer"] = 0.0
owners = owners_of_one_business()
results = {kind: one_year(owner, world) for kind, owner in owners.items()}
check("with nobody to hire, no owner finds any of the crew and each loses the same",
	  {owner.staffed_share("shop") for owner in owners.values()} == {0.0} and len(set(results.values())) == 1 and results["firm"][0] < 0.0, results)

# ---- closing and moving a plant are the business's too ------------------------------------------------
world = make_world()
owners = owners_of_one_business()
firm, player = owners["firm"], owners["player"]
plant = business_closing.release_plant(firm.business, "shop", world)
check("a plant released leaves its owner with nothing of it", "shop" not in firm.concerns and firm.business.plant_of("shop") is None)
player.business.close_plant("shop")
player.receive_plant(plant, world)
check("...and arrives with its size and age", player.capacity_of("shop") == SIZE and player.opened_year_of("shop", 0) == OPENED)

# ---- the business is saved with its owner's record and comes back whole ---------------------------------
owner = owners["player"]
owner.business.note_margin("shop", 12.5)
owner.business.note_crew_found("shop", 0.5)
revived = _deserialize_typed(json.loads(json.dumps(serialize_state(owner.record))), ActorRecord)
check("a business round-trips through save and load with its plants", revived.business == owner.business and isinstance(revived.business, Business)
	  and revived.business.plant_of("shop").margin == 12.5, revived.business)
check("...and the revived business finds its plants by entry", revived.business.size_of("shop") == SIZE and revived.business.plant_of("shop") is not None
      and list(revived.business.entry_keys()) == list(owner.business.entry_keys()))

# ---- switching a plant off keeps it, for any owner ---------------------------------------------------------
owner = owners_of_one_business()["government"]
plant = owner.business.plant_of("shop")
owner.business.mothball("shop", 101, "manual")
check("a mothballed plant is not operating but is kept with its size and age",
	  "shop" not in owner.business.operating() and "shop" in owner.business.mothballed()
	  and owner.business.plant_of("shop") is plant and plant.size == SIZE and plant.opened_year == OPENED)
check("...with the reason and year it was shut", dict(owner.business.closures()) == {"shop": {"reason": "manual", "year": 101}})
owner.business.restore("shop")
check("restoring brings the same plant back", "shop" in owner.business.operating() and plant.state == "operating"
	  and owner.business.plant_of("shop") is plant and not owner.business.closures())
owner.business.mothball("shop", 102, "staff")
revived = _deserialize_typed(json.loads(json.dumps(serialize_state(owner.record))), ActorRecord)
check("a mothballed plant round-trips through a save", revived.business == owner.business
	  and dict(revived.business.closures()) == {"shop": {"reason": "staff", "year": 102}})
