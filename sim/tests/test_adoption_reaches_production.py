"""Complaint 491 remainder: an adoption share weights a plant, conquests and migrations record contact, purchases fill stores."""

QUICK_TOPIC = True

from .harness import check

from sim.agents import adoption, awareness, stock_keeping
from sim.agents.api import ActorRecord, Firm
from sim.engine import contact_events
from sim.labour.api import migrant_pairs, moves_between_regions, totals_of_pairs
from sim.world.demography import Population

check("a plant with no adoption record runs at full weight", adoption.plant_weight({}, "tech") == 1.0)
check("a technique at a share weights its plants by the share",
	  adoption.plant_weight({"tech": {"stage": "trying", "share": 0.25, "since": 1}}, "tech") == 0.25)
check("another technique's share does not weight this one",
	  adoption.plant_weight({"other": {"stage": "adopted", "share": 0.25, "since": 1}}, "tech") == 1.0)
check("a margin is read per unit of share, so a small share is not a small margin",
	  adoption.margin_per_share(5.0, 0.5) == 10.0)
check("a zero weight reads as no margin, not a division by zero", adoption.margin_per_share(5.0, 0.0) == 0.0)

learner = Firm("firm:1", ActorRecord(kind="firm", location="tile_a"))
awareness.record_contacts([learner], ["tile_b", "tile_c"], 2.0)
check("an event's contact is recorded for every place on every receiver", learner.contacts == {"tile_b": 2.0, "tile_c": 2.0})

places = {"previous": ["tile_b", None, "tile_c"], "other": ["tile_z"]}
check("a conquest gives contact with the tile and the overrun country's places only",
	  contact_events.conquest_contacts(places, "previous", "tile_t") == ["tile_b", "tile_c", "tile_t"])
check("a conquest of ground nobody held gives contact with the tile alone",
	  contact_events.conquest_contacts(places, None, "tile_t") == ["tile_t"])

arrivals = contact_events.migrants_arriving([("a", "b", 1000.0), ("a", "b", 500.0), ("c", "b", 0.0)])
check("migrants arriving give the destination contact with the origin in proportion to their number",
	  list(arrivals) == ["b"] and list(arrivals["b"]) == ["a"] and arrivals["b"]["a"] > 0.0)

regions = {"a": Population(children=500.0, working_age=1000.0, elderly=100.0),
		   "b": Population(children=500.0, working_age=1000.0, elderly=100.0)}
fed = {"a": 1.0, "b": 3.0}
borders = {"a": ["b"], "b": ["a"]}
pairs = migrant_pairs(regions, fed, borders, lambda origin, destination: 10.0)
leaving, arriving = moves_between_regions(regions, fed, borders, lambda origin, destination: 10.0)
check("migration pairs name who moved from where to where", any(origin == "a" and destination == "b" for origin, destination, _ in pairs))
check("the regional totals are the sums of the pairs", totals_of_pairs(pairs) == (leaving, arriving))

stores = {"grain": 1.0}
stock_keeping.add_delivery(stores, {"grain": 2.0, "iron": 0.5, "salt": 0.0})
check("delivered goods join the stores", stores == {"grain": 3.0, "iron": 0.5})
check("a firm keeps what it buys", Firm("firm:2", ActorRecord(kind="firm")).keeps_purchases is True)
