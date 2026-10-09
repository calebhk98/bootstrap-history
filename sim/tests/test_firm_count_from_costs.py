"""Complaint 345: the number of firms in a niche follows what a firm must carry (site rent, a manager's
hours, the upkeep and wages of its concern) against what the market pays, with no cap on entrants a
year; entrants judge a market on the takings they expect, not on one year's spike."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, ActorRegistry, ActorsState
from sim.agents import firm_entry

from .agents_fake_world import FakeWorld, make_node

MARKET_TAKINGS = 400000.0


class SharedMarketWorld(FakeWorld):
	"""A niche whose takings are shared among its sellers; a firm also pays rent on its site."""

	def __init__(self, takings=MARKET_TAKINGS, rent=0.0, wage=1.0):
		super().__init__()
		self.takings = takings
		self.rent = rent
		self.labour_market.wage_per_hour = wage
		self.output = 1.0e12
		self.nodes["shop"] = make_node("shop", hours=4000.0, revenue=takings, upkeep=1000.0)
		self.demonstrated_nodes = {"shop"}
		self.proven = {"shop"}

	def entry_gross(self, node_id, rivals, entrants):
		return self.takings / (rivals + entrants)

	def plant_cost(self, node_id, actor, step):
		return 1000.0 * step

	def site_rent(self, node_id, capacity=1.0):
		return self.rent * capacity


def firms_in_one_year(takings=MARKET_TAKINGS, rent=0.0, wage=1.0, existing=0):
	registry = ActorRegistry(ActorsState(home_country="home"))
	for number in range(existing):
		registry.add("firm:%d" % (number + 100), ActorRecord(kind="firm", concerns={"shop"}, founded_year=0))
	return len(registry.consider_entry(SharedMarketWorld(takings, rent, wage)))


# ---- no per-year cap: a market that pays many firms draws them in one year
many = firms_in_one_year()
check("a market that pays several firms draws several in one year", many > 1, many)

# ---- the count follows what a firm carries against what the market pays
check("a dearer site means fewer firms", firms_in_one_year(rent=60000.0) < many, (firms_in_one_year(rent=60000.0), many))
check("a dearer manager means fewer firms", firms_in_one_year(wage=5.0) < many, (firms_in_one_year(wage=5.0), many))
check("a bigger market means more firms", firms_in_one_year(takings=4 * MARKET_TAKINGS) > many,
	(firms_in_one_year(takings=4 * MARKET_TAKINGS), many))
check("a market already served by those firms draws fewer more", firms_in_one_year(existing=many) < many,
	(firms_in_one_year(existing=many), many))
check("a market that pays nothing over its costs draws none", firms_in_one_year(takings=3000.0) == 0)

# ---- what a firm carries is derived, and the stand-in premium is gone
world = SharedMarketWorld(rent=7000.0)
carried = firm_entry.carrying_cost(world, "shop")
check("a firm carries its site rent and a manager's hours", carried > 7000.0, carried)
check("management scales with the staff it supervises",
	firm_entry.management_cost(world, "shop", 2.0) > firm_entry.management_cost(world, "shop", 1.0) > 0.0)
check("the per-operator premium no longer exists", not hasattr(firm_entry, "entry_premium"))


# ---- entrants judge on expected takings: a one-year spike draws fewer than a lasting rise
def entrants_after(years_at_base, takings_now):
	registry = ActorRegistry(ActorsState(home_country="home"))
	for year in range(years_at_base):
		world = SharedMarketWorld()
		world.year = 50 + year
		firm_entry.expected_takings(registry, world, "shop")
	world = SharedMarketWorld(takings=takings_now)
	world.year = 50 + years_at_base
	return len(registry.consider_entry(world))


spike = entrants_after(5, 10 * MARKET_TAKINGS)
lasting = entrants_after(0, 10 * MARKET_TAKINGS)
check("a spike over a settled market draws fewer than the same takings met fresh", spike < lasting, (spike, lasting))


# ---- site rent is the land a concern's declared output takes, at the land market's rent
from sim.engine.agents_port_site import SiteView
from sim.agents.api import supply


class Economy:
	rent = 40.0

	def agent_land_rent_per_hectare(self):
		return self.rent


class Sim:
	economy = Economy()


class Site(SiteView):
	_sim = Sim()
	nodes = {"ag2_sugar_voyage": {"annual_output_t": 120.0}, "no_land": {"annual_output_t": 50.0}}


site = Site()
check("a concern that works land ties up hectares in proportion to its declared output",
	supply.materials_made_by("ag2_sugar_voyage") and site.site_hectares("ag2_sugar_voyage") > 0.0
	and abs(site.site_hectares("ag2_sugar_voyage", 2.0) - 2.0 * site.site_hectares("ag2_sugar_voyage")) < 1e-9,
	site.site_hectares("ag2_sugar_voyage"))
check("its site rent is those hectares at the land market's rent",
	abs(site.site_rent("ag2_sugar_voyage") - 40.0 * site.site_hectares("ag2_sugar_voyage")) < 1e-9)
check("a concern that works no land pays no site rent", site.site_rent("no_land") == 0.0)
