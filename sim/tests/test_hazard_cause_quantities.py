"""Each quantity an event's cause can name: a measured value comes through its reader, an unmeasured one answers None, and the
owners' views that feed it answer what the rule needs (Complaints/266)."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.actors.cause_views import CauseViews
from sim.hazards import cause_report, cause_rules
from sim.hazards.cause_quantities import QUANTITIES
from sim.land.map_views import MapViews


def needs_of(**views):
	"""The module's reads as plain values or functions."""
	return SimpleNamespace(**{name: (value if callable(value) else (lambda value=value: value)) for name, value in views.items()})


def row(members=100.0, welfare=1.0, opening_share=0.5, property_share=0.0, bonded=False):
	return {"members": members, "bonded": bonded, "welfare": welfare, "opening_share": opening_share,
	        "property_share": property_share}


# ---- the rules, on written-out facts
check("a state that needs nothing is fully funded", cause_rules.funded_share(0.0, 0.0) == 1.0)
check("a state short by a quarter of its need is three quarters funded", cause_rules.funded_share(100.0, 25.0) == 0.75)
check("a state short by more than its need is not funded below nothing", cause_rules.funded_share(100.0, 250.0) == 0.0)
check("an army half the wanted size is half of what was wanted", cause_rules.army_share_of_wanted(200.0, 100.0) == 0.5)
check("no wanted army is fully kept", cause_rules.army_share_of_wanted(0.0, 0.0) == 1.0)
check("half the opening tiles still held is a half", cause_rules.territory_share(["a", "x"], ["a", "b"]) == 0.5)
check("no opening tiles is nothing lost", cause_rules.territory_share(["a"], []) == 1.0)
check("output per head is hours over people", cause_rules.output_hours_per_head(500.0, 100.0) == 5.0)
check("output per head is unmeasured with nobody", cause_rules.output_hours_per_head(500.0, 0.0) is None)
check("output per head is unmeasured without a reading", cause_rules.output_hours_per_head(None, 100.0) is None)
strata = [row(10.0, 2.0, 0.01, property_share=0.3), row(900.0, 0.8, 0.9), row(90.0, 0.4, 0.09), row(100.0, 0.1, 0.1, bonded=True),
          row(5.0, None, 0.0)]
check("the lowest welfare is among free strata with a measured welfare", cause_rules.lowest_stratum_welfare(strata) == 0.4)
check("the spread is best over worst", abs(cause_rules.stratum_welfare_spread(strata) - 5.0) < 1e-9)
check("no measured strata, no lowest welfare", cause_rules.lowest_stratum_welfare([row(5.0, None)]) is None)
check("no measured strata, no spread", cause_rules.stratum_welfare_spread([]) is None)
check("a worst welfare of nothing is floored in the spread",
      cause_rules.stratum_welfare_spread([row(1.0, 0.0), row(1.0, 1.0)]) == 1.0 / cause_rules.WORST_WELFARE_FLOOR)
check("an unchanged elite share is 1", abs(cause_rules.elite_share_vs_opening(
	[row(10.0, 1.0, 0.01, property_share=0.3), row(990.0, 1.0, 0.99)]) - 1.0) < 1e-9)
check("a doubled elite share is 2", abs(cause_rules.elite_share_vs_opening(
	[row(20.0, 1.0, 0.01, property_share=0.3), row(980.0, 1.0, 0.99)]) - 2.0) < 1e-9)
check("with no propertied stratum at the opening there is no elite share", cause_rules.elite_share_vs_opening([row()]) is None)

# ---- the readers: a measured value comes through, an unmeasured one is None
def read(name, node=None, **views):
	return QUANTITIES[name].read(needs_of(**views), node)


check("population reads the people", read("population", population_total=1234.0) == 1234.0)
check("output hours per head reads hours and people",
      read("output_hours_per_head", real_output_hours=lambda measure: 800.0, population_total=200.0) == 4.0)
check("output hours per head is None with no people",
      read("output_hours_per_head", real_output_hours=lambda measure: 800.0, population_total=0.0) is None)
check("funded share reads the state's books",
      read("state_funded_share", state_budget_figures={"need": 80.0, "unfunded": 20.0, "coin_metal_kept": 1.0}) == 0.75)
check("army share reads the wanted and kept force",
      read("army_share_of_wanted", army_figures={"wanted": 40.0, "under_arms": 10.0}) == 0.25)
check("general literacy reads the diffusion's figure",
      read("literacy_general", literacy=lambda field, country: {"literacy_general": 0.2}[field]) == 0.2)
check("elite literacy reads the diffusion's figure",
      read("literacy_elite", literacy=lambda field, country: {"literacy_elite": 0.7}[field]) == 0.7)
check("literacy is None when unmeasured", read("literacy_general", literacy=lambda field, country: None) is None)
check("state_holds is 1 when the state knows the node", read("state_holds", "wheel", state_knows=lambda node: node == "wheel") == 1.0)
check("state_holds is 0 when it does not", read("state_holds", "wheel", state_knows=lambda node: False) == 0.0)
check("territory share compares the file's tiles now to the opening's",
      read("territory_share_of_start", civilisation={"id": "now"}, opening_civilisation={"id": "start"},
           tiles_listed_by=lambda civ: ["a"] if civ["id"] == "now" else ["a", "b", "c", "d"]) == 0.25)
check("food supply reads last year's ratio", read("food_supply_ratio", nutrition_ratio_last_year=0.8) == 0.8)
check("food supply is None before the first year", read("food_supply_ratio", nutrition_ratio_last_year=None) is None)
check("coin metal kept reads the state's coin",
      read("coin_metal_kept", state_budget_figures={"need": 1.0, "unfunded": 0.0, "coin_metal_kept": 0.6}) == 0.6)
check("the lowest welfare reads the strata rows", read("lowest_stratum_welfare", home_strata_rows=[row(1.0, 0.3), row(1.0, 2.0)]) == 0.3)
check("the welfare spread reads the strata rows", read("stratum_welfare_spread", home_strata_rows=[row(1.0, 0.5), row(1.0, 2.0)]) == 4.0)
check("the elite share reads the strata rows", abs(read("elite_share_vs_opening", home_strata_rows=[
	row(20.0, 1.0, 0.01, property_share=0.3), row(980.0, 1.0, 0.99)]) - 2.0) < 1e-9)

# ---- judging a cause
cause = {"quantity": "population", "op": ">=", "value": 0.5, "why": "w", "relative_to_start": True}
check("a relative cause is judged against its share of the start value",
      cause_report.judge_cause(cause, 400.0, 1000.0)["holds"] is False
      and cause_report.judge_cause(cause, 600.0, 1000.0)["threshold"] == 500.0)
unjudged = cause_report.judge_cause(cause, 400.0, None)
check("a relative cause with no start value is not judged (it holds, with no value)",
      unjudged["holds"] and unjudged["value"] is None and unjudged["threshold"] is None)
check("an unmeasured reading is not judged", cause_report.judge_cause({**cause, "relative_to_start": False}, None, None)["value"] is None)

# ---- the owners' views feeding the causes
class Record:
	need = {"army": 60.0, "roads": 40.0}
	unfunded = {"army": 10.0}
	coin_metal_kept = 0.9


class Treasury:
	record = Record()

	def knows(self, node_id, world):
		return node_id == "wheel" and world.army_wanted() == 50.0


class ActorsStub(CauseViews):
	def state_treasury(self):
		return Treasury()

	def actor_world(self):
		return SimpleNamespace(army_wanted=lambda: 50.0, soldiers_under_arms=lambda: 30.0)

	def cast(self):
		def stratum(country=None, exited=None, welfare=1.0, reference=1.0, plan=None):
			return SimpleNamespace(record=SimpleNamespace(country=country, exited_year=exited, members=10.0, welfare=welfare,
			                                              welfare_reference=reference, plan=plan or {}))
		return SimpleNamespace(of_kind=lambda kind: [
			stratum(plan={"share": 0.2, "property_share": 0.3}), stratum(welfare=0.5, reference=0.0, plan={"bonded": True}),
			stratum(country="abroad"), stratum(exited=90)])


actors = ActorsStub()
check("the state's books are summed over its lines", actors.state_budget_figures() == {"need": 100.0, "unfunded": 10.0, "coin_metal_kept": 0.9})
check("the army figures are the wanted and kept force", actors.army_figures() == {"wanted": 50.0, "under_arms": 30.0})
check("the state knows what its treasury knows", actors.state_knows("wheel") is True and actors.state_knows("loom") is False)
rows = actors.home_strata_rows()
check("only home strata still in the country are listed", len(rows) == 2)
check("a stratum with no measured welfare answers None", rows[1]["welfare"] is None and rows[0]["welfare"] == 1.0)
check("a row carries the opening plan's shares and bonding",
      rows[0]["opening_share"] == 0.2 and rows[0]["property_share"] == 0.3 and rows[1]["bonded"] is True)


class LandStub(MapViews):
	world_map = SimpleNamespace(tiles={"a": 1, "b": 2, "c": 3})


check("the tiles a file lists are those on the map", LandStub().tiles_listed_by({"home_tiles": ["c", "a", "zz"]}) == ["a", "c"])
