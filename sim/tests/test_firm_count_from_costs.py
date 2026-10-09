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

	def site_rent(self, node_id, capacity=1.0, tile=None):
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


# ---- site rent: every concern occupies a plot from its staff; land it works comes on top
from sim.engine.agents_port_site import SiteView, FLOOR_AREA_PER_WORKER_SQUARE_METRES
from sim.agents.api import supply
from sim.world import merchant_terms


class Economy:
	"""The agent economy's land market: a rent per hectare on each tile where land was let."""
	mean = 40.0
	by_tile = {"coast": 100.0, "hills": 10.0}
	on = True

	def agent_land_rent_at(self, tile):
		if not self.on:
			return None
		return self.by_tile.get(tile, self.mean)


class Sim:
	economy = Economy()


class Site(SiteView):
	_sim = Sim()
	nodes = {"ag2_sugar_voyage": {"annual_output_t": 120.0}, "workshop": {}}
	engine_land_price = 7.0

	def concern_staff(self, node_id):
		return {"artisan": 4.0, "labourer": 6.0}

	def material_price(self, material):
		return self.engine_land_price if material == "hectare_land" else 0.0


site = Site()
plot = site.plot_hectares("workshop")
check("a concern with no declared output still occupies a plot, from its staff at a stated floor area",
	abs(plot - 10.0 * FLOOR_AREA_PER_WORKER_SQUARE_METRES / 10000.0) < 1e-12 and plot > 0.0, plot)
check("a bigger concern occupies a bigger plot", abs(site.plot_hectares("workshop", 3.0) - 3.0 * plot) < 1e-12)
check("a concern that works land ties up the land and the plot",
	supply.materials_made_by("ag2_sugar_voyage") and site.site_hectares("ag2_sugar_voyage") > site.plot_hectares("ag2_sugar_voyage")
	and abs(site.site_hectares("workshop") - plot) < 1e-12, site.site_hectares("ag2_sugar_voyage"))
check("rent is the hectares at the rent of the tile the concern stands on",
	abs(site.site_rent("workshop", tile="coast") - 100.0 * plot) < 1e-9
	and abs(site.site_rent("workshop", tile="hills") - 10.0 * plot) < 1e-9)
check("a tile where no land was let pays the mean rent of the land let", abs(site.site_rent("workshop", tile="moor") - 40.0 * plot) < 1e-9)
check("a dearer tile costs more", site.site_rent("workshop", tile="coast") > site.site_rent("workshop", tile="hills"))
Economy.on = False
check("while the economy opens the rent is the engine's land price", abs(site.site_rent("workshop", tile="coast") - 7.0 * plot) < 1e-9)
Economy.on = True

# ---- where a firm stands: its own tile, else the home country's
registry = ActorRegistry(ActorsState(home_country="home"))
registry.add("government:home", ActorRecord(kind="government", location="coast"))
check("a firm with no tile of its own stands on the home country's tile", firm_entry.firm_tile(registry, None) == "coast")
firm = registry.add("firm:7", ActorRecord(kind="firm", concerns={"shop"}, location="hills"))
check("a firm stands where it was placed", firm_entry.firm_tile(registry, firm) == "hills")
check("no home government, no tile", firm_entry.firm_tile(ActorRegistry(ActorsState(home_country="home")), None) is None)


class TileWorld(SharedMarketWorld):
	def site_rent(self, node_id, capacity=1.0, tile=None):
		return {"coast": 90000.0, "hills": 1000.0}.get(tile, 0.0) * capacity


world = TileWorld()
check("a firm carries the rent of its own tile", firm_entry.carrying_cost(world, "shop", tile="coast")
	> firm_entry.carrying_cost(world, "shop", tile="hills"))
entry_registry = ActorRegistry(ActorsState(home_country="home"))
entry_registry.add("government:home", ActorRecord(kind="government", location="hills"))
founded = entry_registry.consider_entry(TileWorld())
check("a firm founded by entry is placed on a tile", founded and all(
	entry_registry.get(firm_id).record.location == "hills" for firm_id in founded), founded)

# ---- the cost of winning customers: the merchants' agents are paid per tonne a carrier lifts
check("a sale that needs no carrier needs no agents on the model's terms",
	merchant_terms.agent_cost_per_tonne(None, 2000.0, 1.0, 2.0) == 0.0)
check("a sale across a route costs the agents' hours the lift takes, at the going wage",
	abs(merchant_terms.agent_cost_per_tonne(0.01, 2000.0, 3.0, 2.0) - 2.0 * 0.01 * 2000.0 * 3.0) < 1e-9)
