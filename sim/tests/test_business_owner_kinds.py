"""One business, run by a firm, a player and a state, has the same crew, upkeep, takings and books.

Stage 1 of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md: what differs between owners is who decides, never the arithmetic."""

QUICK_TOPIC = True

import json

from .harness import check

from sim.agents import business_books, business_closing
from sim.agents.business_plant import Plant
from sim.agents.api import ActorRecord, ActorRegistry, ActorsState, Business
from sim.engine.state import _deserialize_typed, serialize_state

from .agents_fake_world import FakeWorld, make_node

OWNER_KINDS = ("firm", "player", "government")
SIZE = 2.5
OPENED = 95
OPENING_MONEY = 5000.0


def make_world():
	world = FakeWorld(year=100)
	world.setting.nodes["shop"] = make_node("shop", hours=4000.0, revenue=20000.0, upkeep=60.0)
	return world


def owners_of_one_business(world, crew_found=True):
	"""One plant per owner kind; `crew_found` gives each the people the labour core would have hired for it."""
	registry = ActorRegistry(ActorsState(home_country="home"))
	owners = {}
	for kind in OWNER_KINDS:
		owner = registry.add("%s:1" % kind, ActorRecord(kind=kind, money=OPENING_MONEY, founded_year=90))
		owner.business.lifecycle.adopt(Plant("shop", opened_year=OPENED, size=SIZE))
		if crew_found:
			owner.record.workforce.update({trade: people * SIZE for trade, people in world.concerns.concern_staff("shop").items()})
		owners[kind] = owner
	return owners


def one_year(owner, world):
	margin = business_books.operate(owner.business, owner, "shop", world, 1.0)
	carried = business_books.carry(owner.business, owner, "shop", world)
	return margin, carried


world = make_world()
owners = owners_of_one_business(world)
results = {kind: one_year(owner, world) for kind, owner in owners.items()}
check("the three owners' businesses are the same plant", len({tuple((plant.entry_key, plant.size, plant.opened_year)
	  for plant in owner.business.plants) for owner in owners.values()}) == 1)
check("the same year gives the same margin and carrying cost to a firm, a player and a state",
	  len(set(results.values())) == 1 and results["firm"][0] > 0.0, results)
check("it posts the same places for its crew", len({tuple(sorted(owner.staff_wanted.items())) for owner in owners.values()}) == 1
	  and owners["firm"].staff_wanted["labourer"] >= world.concerns.concern_staff("shop")["labourer"] * SIZE, owners["firm"].staff_wanted)
check("it finds the same share of its crew", len({owner.holdings.staffed_share("shop") for owner in owners.values()}) == 1)
check("it pays the same: money after the year is the same", len({round(owner.money, 9) for owner in owners.values()}) == 1)
expected = OPENING_MONEY + world.concerns.concern_takings("shop", OPENED, 1.0, SIZE) - world.concerns.upkeep("shop", SIZE) \
	- world.site.site_rent("shop", SIZE)
check("takings less upkeep and site rent is what the purse gained (the crew and the managers are posted to the labour market and paid by its clearing, not here)", all(abs(owner.money - expected) < 1e-6 for owner in owners.values()),
	  [owner.money for owner in owners.values()])
check("the books balance per owner: purse = opening + income - outlays",
	  all(abs(owner.money - (OPENING_MONEY + sum(owner.record.income.values()) - sum(owner.record.outlays.values()))) < 1e-6
		  for owner in owners.values()))

# ---- a crew the labour core did not hire makes less, for every owner alike ----------------------------------
owners = owners_of_one_business(world, crew_found=False)
results = {kind: one_year(owner, world) for kind, owner in owners.items()}
check("with nobody hired, no owner finds any of the crew and each loses the same",
	  {owner.holdings.staffed_share("shop") for owner in owners.values()} == {0.0} and len(set(results.values())) == 1 and results["firm"][0] < 0.0, results)

# ---- closing and moving a plant are the business's too ------------------------------------------------
world = make_world()
owners = owners_of_one_business(world)
firm, player = owners["firm"], owners["player"]
plant = business_closing.release_plant(firm.business, "shop", world)
check("a plant released leaves its owner with nothing of it", "shop" not in firm.concerns and firm.business.reading.plant_of("shop") is None)
player.business.lifecycle.close_plant("shop")
player.holdings.receive_plant(plant, world)
check("...and arrives with its size and age", player.holdings.capacity_of("shop") == SIZE and player.holdings.opened_year_of("shop", 0) == OPENED)

# ---- the business is saved with its owner's record and comes back whole ---------------------------------
owner = owners["player"]
owner.business.tally.note_margin("shop", 12.5)
owner.business.tally.note_crew_found("shop", 0.5)
revived = _deserialize_typed(json.loads(json.dumps(serialize_state(owner.record))), ActorRecord)
check("a business round-trips through save and load with its plants", revived.business == owner.business and isinstance(revived.business, Business)
	  and revived.business.reading.plant_of("shop").margin == 12.5, revived.business)
check("...and the revived business finds its plants by entry", revived.business.reading.size_of("shop") == SIZE and revived.business.reading.plant_of("shop") is not None
      and list(revived.business.reading.entry_keys()) == list(owner.business.reading.entry_keys()))

# ---- switching a plant off keeps it, for any owner ---------------------------------------------------------
owner = owners_of_one_business(world)["government"]
plant = owner.business.reading.plant_of("shop")
owner.business.lifecycle.mothball("shop", 101, "manual")
check("a mothballed plant is not operating but is kept with its size and age",
	  "shop" not in owner.business.operating() and "shop" in owner.business.mothballed()
	  and owner.business.reading.plant_of("shop") is plant and plant.size == SIZE and plant.opened_year == OPENED)
check("...with the reason and year it was shut", dict(owner.business.closures()) == {"shop": {"reason": "manual", "year": 101}})
owner.business.lifecycle.restore("shop")
check("restoring brings the same plant back", "shop" in owner.business.operating() and plant.state == "operating"
	  and owner.business.reading.plant_of("shop") is plant and not owner.business.closures())
owner.business.lifecycle.mothball("shop", 102, "staff")
revived = _deserialize_typed(json.loads(json.dumps(serialize_state(owner.record))), ActorRecord)
check("a mothballed plant round-trips through a save", revived.business == owner.business
	  and dict(revived.business.closures()) == {"shop": {"reason": "staff", "year": 102}})
