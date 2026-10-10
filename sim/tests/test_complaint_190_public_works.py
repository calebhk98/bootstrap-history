"""Complaint 190: works repeated across the land and what they do to the nation as a whole. Coverage and rollouts,
district clinics against the disease burden, grain handed out to a hungry nation, a free press wearing away the
state's authority, schools that teach one group, and light that lengthens the working day."""
from .harness import *  # noqa: F401,F403

from sim.engine.core import TECH_EFFECTS, demography
from sim.engine.agents_port import SimWorld
from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.world.shared_constants import WHEAT_ENERGY_KCAL_PER_KG

CLINICS, VILLAGE, COLLEGE, DOLE, PRESS, LIGHTS, FREE_SCHOOL = (
    "ben_district_clinics", "ben_village_schools", "ben_endowed_college", "ben_grain_dole", "ben_free_press",
    "ben_city_electric_lighting", "ben_free_school_foundation")


def running(node_id, units=1.0, capital=1.0e12):
    """A game, the economy unopened, in which `node_id` is built and open at `units`."""
    game = unopened_sim(capital=capital)
    game.done.update(NODES[node_id]["pre"])
    game.done.add(node_id)
    game._done_changed()
    game.state.projects.operating.add(node_id)
    if "schooling_flow" in NODES[node_id]["mechanics"]:
        game.state.projects.operating.add("school_founded")   # no school teaches where the original school is shut
    set_units(game, node_id, units)
    return game


def set_units(game, node_id, units):
    game.state.governance.inst_units = dict(game.state.governance.inst_units or {})
    game.state.governance.inst_units[node_id] = units
    game.household.bump_institution_units_version()
    game._done_changed()


# ---- coverage: what share of the people a repeated work serves -----------------------------------------
game = running(CLINICS)
hours = sum(NODES[CLINICS]["annual_labour_hours"].values())
per_unit = hours / NODES[CLINICS]["mechanics"]["coverage"]["staff_hours_per_person_year"]
check("a clinic unit serves its staff hours over the hours each patient needs",
      abs(game.people_per_unit(CLINICS) - per_unit) < 1e-9, (game.people_per_unit(CLINICS), per_unit))
check("one unit covers its people over the nation's",
      abs(game.coverage_share(CLINICS) - per_unit / game.population.total) < 1e-12, game.coverage_share(CLINICS))
check("coverage counts only while the doors are open",
      unopened_sim().coverage_share(CLINICS) == 0.0)
half_units = game.units_for_coverage(CLINICS, 0.5)
set_units(game, CLINICS, half_units)
check("the units that serve half the people do", abs(game.coverage_share(CLINICS) - 0.5) < 1e-9, game.coverage_share(CLINICS))
check("the most units the nation can fill is the units that serve everyone, not a few towns' worth",
      abs(game.institution_unit_ceiling(CLINICS) - game.units_for_coverage(CLINICS, 1.0)) < 1e-9,
      (game.institution_unit_ceiling(CLINICS), game.units_for_coverage(CLINICS, 1.0)))
check("a work cannot cover more than everyone", abs(game.units_for_coverage(CLINICS, 1.0) * per_unit - game.population.total) < 1e-3)

schools = running(VILLAGE)
eligible = NODES[VILLAGE]["mechanics"]["coverage"]["eligible_share"]
check("a school is measured against the school-age share of the people, not all of them",
      abs(schools.units_for_coverage(VILLAGE, 1.0) * schools.people_per_unit(VILLAGE)
          - eligible * schools.population.total) < 1e-3, schools.units_for_coverage(VILLAGE, 1.0))

# ---- district clinics lower the nation's disease burden by the share they reach ----------------------
weights = {tech_id: TECH_EFFECTS[tech_id]["population"] for tech_id in game.DISEASE_BURDEN_TECH_IDS}
total = sum(weights.values())
check("district clinics carry a weight in the disease-burden table", CLINICS in weights and weights[CLINICS] > 0, weights)
expected = 1.0 - weights[CLINICS] * 0.5 / total
check("clinics reaching half the people take half their weight off the burden",
      abs(game._disease_burden() - expected) < 1e-12, (game._disease_burden(), expected))
set_units(game, CLINICS, game.units_for_coverage(CLINICS, 1.0))
check("clinics reaching everyone take all their weight off the burden",
      abs(game._disease_burden() - (1.0 - weights[CLINICS] / total)) < 1e-12, game._disease_burden())

built_not_open = unopened_sim()
built_not_open.done.update(NODES[CLINICS]["pre"])
built_not_open.done.add(CLINICS)
built_not_open._done_changed()
check("clinics built but shut take nothing off the burden",
      built_not_open._disease_burden() == demography.PRE_INDUSTRIAL_DISEASE_BURDEN, built_not_open._disease_burden())

everything = unopened_sim()
everything.done.update(everything.DISEASE_BURDEN_TECH_IDS)
everything._done_changed()
check("every other disease technology held and no clinic open leaves only the clinics' share of the burden",
      abs(everything._disease_burden() - weights[CLINICS] / total) < 1e-12, everything._disease_burden())
check("a technology that declares no coverage still counts whole once held",
      everything.disease_burden_held("germ_theory") == 1.0)

tiny = running(CLINICS, units=1.0)
check("one clinic does almost nothing for a nation", 1.0 - tiny._disease_burden() < 0.001 * weights[CLINICS] / total + 1e-9,
      tiny._disease_burden())

# a benefit that holds only while the doors are open and for the share reached is not promised as permanent
from sim.engine.permanent_benefit import permanent_parts

check("a knowledge node's disease benefit is permanent", any("disease" in part for part in permanent_parts(
      NODES["germ_theory"], TECH_EFFECTS["germ_theory"])), permanent_parts(NODES["germ_theory"], TECH_EFFECTS["germ_theory"]))
check("clinics' disease benefit is not called permanent", not any("disease" in part for part in permanent_parts(
      NODES[CLINICS], TECH_EFFECTS[CLINICS])), permanent_parts(NODES[CLINICS], TECH_EFFECTS[CLINICS]))
finished = unopened_sim()
finished.done.add(CLINICS)
finished.apply_tech_effects(CLINICS)
check("finishing the clinics does not announce a lower disease burden before any clinic is open",
      not any("disease burden" in line for _year, line in finished.state.household.log), finished.state.household.log[-2:])

# ---- the rollout opens the units a share needs -------------------------------------------------------------
asked = []


def record(node_id, pay=True, units=None):
    asked.append((node_id, units))
    return True, "%s opened" % node_id


fresh = unopened_sim(capital=1.0e12)
fresh.done.update(NODES[CLINICS]["pre"])
fresh.done.add(CLINICS)
fresh._done_changed()
fresh.open_venture = record
ok, text = fresh.roll_out(CLINICS, 0.1)
check("rolling out a work not yet open opens it at the units the share needs",
      ok and asked == [(CLINICS, fresh.units_for_coverage(CLINICS, 0.1))], (ok, text, asked))
asked.clear()
partway = running(CLINICS, units=3.0)
partway.open_venture = record
ok, text = partway.roll_out(CLINICS, 0.1)
check("rolling out an open work adds only the units still wanted",
      ok and abs(asked[0][1] - (partway.units_for_coverage(CLINICS, 0.1) - 3.0)) < 1e-9, (ok, asked))
asked.clear()
ok, text = partway.roll_out(CLINICS, 0.0001)
check("a share already covered asks for nothing", not ok and asked == [] and "already covers" in text, (ok, text, asked))
check("a work that cannot be rolled out is refused", not unopened_sim().roll_out("blast_furnace", 0.5)[0])
check("a work not yet known is refused without naming it", unopened_sim().roll_out(CLINICS, 0.5) == (
    False, "you have not worked out how to do that yet"))

listing = S._agent_dispatch(running(CLINICS), NODES, {"cmd": "rollout"})
row = listing["rollouts"][0] if listing.get("rollouts") else {}
check("`rollout` lists the works with coverage, units open and the units that serve everyone",
      listing.get("ok") and row.get("id") == CLINICS and row["units"] == 1.0 and row["units_for_everyone"] > 1000, listing)
check("`rollout` with a share but no known work is refused",
      S._agent_dispatch(unopened_sim(), NODES, {"cmd": "rollout", "id": CLINICS, "share": 0.5})["ok"] is False)
check("`rollout` with a share beyond everyone is refused",
      S._agent_dispatch(running(CLINICS), NODES, {"cmd": "rollout", "id": CLINICS, "share": 150})["ok"] is False)

from sim.ui.proto.typed import parse_typed

check("the typed line `rollout <id> 50` reads",
      parse_typed("rollout %s 50" % CLINICS)[0] == {"cmd": "rollout", "id": CLINICS, "share": 50.0}, parse_typed("rollout %s 50" % CLINICS))
check("the typed line `rollout` alone lists", parse_typed("rollout")[0] == {"cmd": "rollout"})

# ---- grain handed out to the nation: the people eat it on top of the harvest --------------------------------
dole = running(DOLE)
kilograms = NODES[DOLE]["annual_consumables"]["wheat_kg"]
spec = NODES[DOLE]["mechanics"]["food_relief"]
check("the grain dole's energy per kilogram is wheat's", spec["energy_kcal_per_kg"] == WHEAT_ENERGY_KCAL_PER_KG,
      (spec["energy_kcal_per_kg"], WHEAT_ENERGY_KCAL_PER_KG))
check("an open grain dole hands out the grain it buys, as calories a day",
      abs(dole.relief_kcal_per_day() - kilograms * WHEAT_ENERGY_KCAL_PER_KG / 365.0) < 1e-6, dole.relief_kcal_per_day())
set_units(dole, DOLE, 3.0)
check("more units hand out more", abs(dole.relief_kcal_per_day() - 3 * kilograms * WHEAT_ENERGY_KCAL_PER_KG / 365.0) < 1e-6)
check("no dole open hands out nothing", unopened_sim().relief_kcal_per_day() == 0.0)

people = demography.Population.stationary(1.0e6)
hungry_food = 0.6 * people._subsistence_food()
without = people.copy()
flows_without = without.step(hungry_food, jitter=False)
with_relief = people.copy()
flows_with = with_relief.step(hungry_food + 0.2 * people._subsistence_food(), jitter=False)
check("a hungry nation that is handed food loses fewer people", flows_with.deaths < flows_without.deaths,
      (flows_with.deaths, flows_without.deaths))

# ---- a free press wears away the state's authority ------------------------------------------------------------
plain = unopened_sim()
check("with no work declaring it, the state keeps all its capacity",
      plain.state_legitimacy() == 1.0 and plain.state_authority() == plain.state_capacity, plain.state_legitimacy())
press = running(PRESS, units=4.0)
check("an open free press lowers the share of its capacity the state keeps",
      abs(press.state_legitimacy() - (1.0 - 0.02 * 4.0 ** 0.5)) < 1e-12, press.state_legitimacy())
check("the state's authority is its capacity times that share", abs(press.state_authority() - press.state_capacity * press.state_legitimacy()) < 1e-12)
check("what the state's budget and enforcement ask of the world is the authority",
      SimWorld(press).state_capacity() == press.state_authority(), SimWorld(press).state_capacity())
huge = running(PRESS, units=1.0e6)
check("however many presses, the state keeps some of its capacity", huge.state_legitimacy() == 0.5, huge.state_legitimacy())

# ---- schooling that teaches one group -------------------------------------------------------------------------------
def gains(node_id=None):
    """(general, elite) literacy the next year adds, with the original school open and `node_id` as well."""
    taught = running(node_id) if node_id else unopened_sim()
    taught.done.add("school_founded")
    taught.state.projects.operating.add("school_founded")
    taught._done_changed()
    taught.civ["literacy_general"], taught.civ["literacy_elite"] = 0.05, 0.4
    moved = taught.literacy_next_year()
    return moved.get("literacy_general", 0.05) - 0.05, moved.get("literacy_elite", 0.4) - 0.4


base_general, base_elite = gains()
check("the original school teaches both groups", base_general > 0 and base_elite > 0, (base_general, base_elite))
general, elite = gains(VILLAGE)
check("schools in every parish add to the teaching of the many and not of the lettered few",
      general > base_general and abs(elite - base_elite) < 1e-12, (general, elite, base_general, base_elite))
general, elite = gains(COLLEGE)
check("an endowed college adds to the teaching of the lettered and not of the many",
      elite > base_elite and abs(general - base_general) < 1e-12, (general, elite, base_general, base_elite))
general, elite = gains(FREE_SCHOOL)
check("a school that names no group adds to both, as before", general > base_general and elite > base_elite,
      (general, elite))
both = running(VILLAGE)
set_units(both, COLLEGE, 1.0)
both.done.update(NODES[COLLEGE]["pre"])
both.done.add(COLLEGE)
both.state.projects.operating.add(COLLEGE)
both._done_changed()
check("each figure moves with the schools that teach it",
      abs(both.effective_schooling_flow("literacy_general") - both.effective_schooling_flow("literacy_elite")) > 1e-9
      and both.effective_schooling_flow() > both.effective_schooling_flow("literacy_general"),
      (both.effective_schooling_flow("literacy_general"), both.effective_schooling_flow("literacy_elite"), both.effective_schooling_flow()))

# ---- light lengthens the working day for the people it reaches ---------------------------------------------------
check("with no lit streets the year is the convention", unopened_sim().HOURS_PER_PERSON_YEAR == HOURS_PER_PERSON_YEAR)
lit = running(LIGHTS)
set_units(lit, LIGHTS, lit.units_for_coverage(LIGHTS, 0.5))
extra = NODES[LIGHTS]["mechanics"]["working_day"]["extra_hours_per_day"]
check("lights over half the people add half the lit hours to the day",
      abs(lit.extra_lit_hours_per_day() - 0.5 * extra) < 1e-9, lit.extra_lit_hours_per_day())
check("a longer day gives every wage quote, head count and hours ledger a longer year",
      abs(lit.HOURS_PER_PERSON_YEAR - HOURS_PER_PERSON_YEAR * (1.0 + 0.5 * extra / 10.0)) < 1e-9
      and lit.labour._world.HOURS_PER_PERSON_YEAR == lit.HOURS_PER_PERSON_YEAR, lit.HOURS_PER_PERSON_YEAR)
shut = unopened_sim()
shut.done.update(NODES[LIGHTS]["pre"])
shut.done.add(LIGHTS)
shut._done_changed()
check("lights built but not lit add nothing", shut.HOURS_PER_PERSON_YEAR == HOURS_PER_PERSON_YEAR, shut.HOURS_PER_PERSON_YEAR)
