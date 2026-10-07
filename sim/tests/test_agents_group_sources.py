"""Interest groups beyond displaced material producers: strata whose incomes fall (311), the society's own
producers of a goods category the founder's concerns undersell (312), and what a prohibition reaches (313)."""
from .harness import check, sim

from sim.agents.api import ActorRegistry, ActorsState, CountryProfile, Sector
from sim.agents.group import blame_after_protection, protection_needed
from sim.agents.group_reach import subjects_reached
from sim.agents.strata_seed import strata_spawner
from sim.agents.tuning_strata import STRATUM_WORKING_SHARE
from sim.engine.agents_port import SimWorld

from .agents_fake_world import FakeWorld


class StrataWorld(FakeWorld):

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.pay = {"labourer": 150.0, "artisan": 400.0}

	def subsistence_cost_per_person_year(self):
		return 100.0

	def need_floor_costs_per_person_year(self):
		return {"food": 100.0, "shelter": 40.0}

	def pay_per_person_year(self, trade):
		return self.pay[trade]

	def observed_stratum(self, country, name):
		return None


DEFINITIONS = [{"name": "toilers", "share": 0.6, "trade": "labourer"},
			   {"name": "weavers", "share": 0.2, "trade": "artisan"},
			   {"name": "owners", "share": 0.01, "property_share": 0.3},
			   {"name": "serfs", "share": 0.1, "bonded": True, "owner": "owners"}]


def build():
	state = ActorsState(home_country="home")
	state.countries["home"] = CountryProfile(country="home", population=100000.0, strata=DEFINITIONS)
	registry = ActorRegistry(state)
	world = StrataWorld()
	strata_spawner(registry, world)
	return registry, world


def stratum(registry, name):
	return registry.actors["stratum:home:" + name]


# ---- 311: a stratum whose welfare falls below what it has been organises --------------------
registry, world = build()
strata = registry.of_kind("stratum")
for actor in strata:
	actor.record.welfare = 1.5
Sector.remember_welfare(strata)
steady = Sector.of_strata(strata, world)
check("steady incomes organise nobody", steady == [], [sector.subject for sector in steady])
toilers = stratum(registry, "toilers").record
toilers.welfare = 0.75
stratum(registry, "weavers").record.welfare = 1.49
stratum(registry, "serfs").record.welfare = 0.0
fallen = {sector.subject: sector for sector in Sector.of_strata(strata, world)}
check("a stratum whose welfare has fallen from what it was forms a sector of falling incomes",
	  "toilers" in fallen and fallen["toilers"].kind == "falling_incomes", list(fallen))
expected = toilers.members * 100.0 * (1.5 - 0.75)
check("the loss is the fall in welfare times the food bill of its people",
	  abs(fallen["toilers"].lost_income - expected) < 1e-6 * expected, (fallen["toilers"].lost_income, expected))
check("people held in bond cannot organise", "serfs" not in fallen, list(fallen))
check("the group speaks for the stratum's own people", abs(fallen["toilers"].members - toilers.members) < 1e-6)
stratum(registry, "owners").record.welfare = 0.5
rents = {sector.subject: sector for sector in Sector.of_strata(strata, world)}
check("a propertied stratum whose property income falls speaks of its rents",
	  "owners" in rents and "rents" in rents["owners"].cause, rents.get("owners") and rents["owners"].cause)
for _year in range(60):
	Sector.remember_welfare(strata)
settled = Sector.of_strata(strata, world)
check("a fall that lasts becomes the new normal and the grievance fades",
	  all(sector.lost_income < 1e-4 * sector.income_base for sector in settled), [s.lost_income for s in settled])

# ---- 312: the society's producers of a goods category lose to the price the founder's concerns bring ----
registry, world = build()
strata = registry.of_kind("stratum")
categories = {"textiles": {"price_depression": 0.3, "trade_weights": {"artisan": 0.5}},
			  "printing": {"price_depression": 0.0, "trade_weights": {"artisan": 0.5}},
			  "sound": {"price_depression": 0.4, "trade_weights": {"smith": 1.0}}}
goods = {sector.subject: sector for sector in Sector.of_goods(strata, categories, world)}
weavers = stratum(registry, "weavers").record
income = weavers.members * STRATUM_WORKING_SHARE * 400.0 * 0.5
check("a category whose price the founder's concerns depress organises the strata that make it",
	  list(goods) == ["textiles"] and goods["textiles"].kind == "displaced_producers", list(goods))
check("their loss is the depression times what the trade earns in the category",
	  abs(goods["textiles"].lost_income - 0.3 * income) < 1e-6 * income, (goods["textiles"].lost_income, income))
check("an undepressed category and one no stratum works in form no group", "printing" not in goods and "sound" not in goods)
check("the founder is blamed for the whole depression when his are the only concerns selling into the category",
	  goods["textiles"].blame_share == 1.0, goods["textiles"].blame_share)
shared = {"textiles": {"price_depression": 0.3, "trade_weights": {"artisan": 0.5}, "founder_share": 0.25}}
check("the founder is blamed only for his share of the sellers when firms sell into the category too",
	  Sector.of_goods(strata, shared, world)[0].blame_share == 0.25, Sector.of_goods(strata, shared, world)[0].blame_share)

# ---- 436: firms selling into a category share the blame for its price depression -------------------
game = sim()
category = "textiles"
node_id = game._nodes_in_cat(category)[0]
game.done.add(node_id)
game._done_changed()
game.operating.add(node_id)
game._operating_changed()
game.actor_concerns_in = lambda asked: 3.0 if asked == category else 0
game.household._goods_cat_state_cache = None
game.household._goods_category_ratios_cache = None
founder_share = SimWorld(game).goods_categories()[category]["founder_share"]
check("the founder's share of a depressed category is his concerns over every seller's, firms included",
	  abs(founder_share - 0.25) < 1e-9, founder_share)

# ---- 313: a prohibition is bargained down by protection, not lifted outright ---------------------
check("a weak group is overridden by little protection, a strong one needs more",
	  protection_needed(0.2, 0.5) < protection_needed(0.9, 0.5) <= 1.0,
	  (protection_needed(0.2, 0.5), protection_needed(0.9, 0.5)))
check("protection at the line suffices only against a group with no pull", abs(protection_needed(0.0, 0.5) - 0.5) < 1e-9)
check("blame from a group is scaled by the founder's share of its loss",
	  blame_after_protection(10.0, 0.0, 0.5) < blame_after_protection(10.0, 0.0, 1.0))

# ---- 313: what a node reaches ---------------------------------------------------------------------
nodes = {"loom": {"cat": "textiles", "pre": []}, "mill": {"cat": "textiles", "pre": ["loom"]},
		 "forge": {"cat": "metallurgy", "pre": []}, "bridge": {"cat": "civil", "pre": ["loom"]}}
makes = {"loom": ["cloth_kg"]}
def made_by(node_id):
	return makes.get(node_id, [])
reached = subjects_reached("mill", nodes, made_by, lambda material: "cloth")
check("a node reaches its own goods category and the commodity a node it refines makes",
	  reached == {"cloth", "textiles"}, reached)
check("a node of another line that merely needs the loom is not reached",
	  "cloth" not in subjects_reached("bridge", nodes, made_by, lambda material: "cloth"))
check("a node making nothing reaches only its own category",
	  subjects_reached("forge", nodes, made_by, lambda material: material) == {"metallurgy"})
