"""SCENARIO (Complaint 190): in a whole game, wiring only for coverage, burden and rollout (their rules are in
test_coverage_rules), works repeated across the land change the nation as a whole: coverage and
rollouts, district clinics against the disease burden, a free press wearing away
the state's authority, schools that teach one group, and light that lengthens the working day. The permanence of a
benefit, the typed lines and the demography of a fed nation are in test_complaint_190_public_works."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of

from sim.engine.core import TECH_EFFECTS, demography
from sim.engine.agents_port import SimWorld
from sim.unit_conversions import HOURS_PER_PERSON_YEAR

CLINICS, VILLAGE, COLLEGE, PRESS, LIGHTS, FREE_SCHOOL = (
    "ben_district_clinics", "ben_village_schools", "ben_endowed_college", "ben_free_press",
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
    game.state.projects.business.set_size(node_id, units)
    game.household.bump_institution_units_version()
    game._done_changed()


# ---- coverage: what share of the people a repeated work serves -----------------------------------------
game = running(CLINICS)
check("coverage counts only while the doors are open",
      unopened_sim().coverage_share(CLINICS) == 0.0)
half_units = game.units_for_coverage(CLINICS, 0.5)
set_units(game, CLINICS, half_units)
check("a game's open clinics serve the share its units ask for", abs(game.coverage_share(CLINICS) - 0.5) < 1e-9, game.coverage_share(CLINICS))
check("the most units the nation can fill is the units that serve everyone, not a few towns' worth",
      abs(game.institution_unit_ceiling(CLINICS) - game.units_for_coverage(CLINICS, 1.0)) < 1e-9,
      (game.institution_unit_ceiling(CLINICS), game.units_for_coverage(CLINICS, 1.0)))

# ---- district clinics lower the nation's disease burden by the share they reach ----------------------
weights = {tech_id: TECH_EFFECTS[tech_id]["population"] for tech_id in game.DISEASE_BURDEN_TECH_IDS}
total = sum(weights.values())
check("district clinics carry a weight in the disease-burden table", CLINICS in weights and weights[CLINICS] > 0, weights)
check("clinics reaching half the people lower the burden a game reads",
      game._disease_burden() < demography.PRE_INDUSTRIAL_DISEASE_BURDEN, game._disease_burden())
set_units(game, CLINICS, game.units_for_coverage(CLINICS, 1.0))

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

finished = unopened_sim()
finished.done.add(CLINICS)
finished.apply_tech_effects(CLINICS)
check("finishing the clinics does not announce a lower disease burden before any clinic is open",
      not any("population" in facts_of(line).get("fields", ()) for _year, line in finished.state.household.log),
      finished.state.household.log[-2:])

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
check("a share already covered asks for nothing here either", not partway.roll_out(CLINICS, 0.0001)[0] and asked == [])
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

# ---- a free press wears away the state's authority ------------------------------------------------------------
plain = unopened_sim()
check("with no work declaring it, the state keeps all its capacity",
      plain.state_legitimacy() == 1.0 and plain.state_authority() == plain.state_reach(), plain.state_legitimacy())
press = running(PRESS, units=4.0)
check("the state's authority is its capacity times that share", abs(press.state_authority() - press.state_reach() * press.state_legitimacy()) < 1e-12)
check("what the state's budget and enforcement ask of the world is the authority",
      SimWorld(press).state_reach() == press.state_authority(), SimWorld(press).state_reach())

# ---- schooling that teaches one group -------------------------------------------------------------------------------
def gains(node_id=None):
    """The common and propertied strata's gains, with the original school and `node_id` open."""
    taught = running(node_id) if node_id else unopened_sim()
    taught.done.add("school_founded")
    taught.state.projects.operating.add("school_founded")
    taught._done_changed()
    taught.set_literacy("literacy_general", 0.05)
    taught.set_literacy("literacy_elite", 0.4)
    def shares():
        common = [record for record in taught.country_literacy().records
                  if float(record.plan.get("property_share") or 0.0) <= 0.0]
        people = sum(record.members for record in common)
        return (sum(record.members * record.literacy for record in common) / people,
                taught.literacy("literacy_elite"))
    before_general, before_elite = shares()
    taught._advance_literacy(taught.year)
    after_general, after_elite = shares()
    return after_general - before_general, after_elite - before_elite


base_general, base_elite = gains()
check("the original school teaches both groups", base_general > 0 and base_elite > 0, (base_general, base_elite))
general, elite = gains(VILLAGE)
check("schools in every parish add to the teaching of the many and not of the lettered few",
      general > base_general and abs(elite - base_elite) < 1e-12, (general, elite, base_general, base_elite))

# ---- light lengthens the working day for the people it reaches ---------------------------------------------------
check("with no lit streets the year is the convention", unopened_sim().HOURS_PER_PERSON_YEAR == HOURS_PER_PERSON_YEAR)
lit = running(LIGHTS)
set_units(lit, LIGHTS, lit.units_for_coverage(LIGHTS, 0.5))
extra = NODES[LIGHTS]["mechanics"]["working_day"]["extra_hours_per_day"]
check("a longer day gives every wage quote, head count and hours ledger a longer year",
      abs(lit.HOURS_PER_PERSON_YEAR - HOURS_PER_PERSON_YEAR * (1.0 + 0.5 * extra / 10.0)) < 1e-9
      and lit.labour._world.HOURS_PER_PERSON_YEAR == lit.HOURS_PER_PERSON_YEAR, lit.HOURS_PER_PERSON_YEAR)
shut = unopened_sim()
shut.done.update(NODES[LIGHTS]["pre"])
shut.done.add(LIGHTS)
shut._done_changed()
check("lights built but not lit add nothing", shut.HOURS_PER_PERSON_YEAR == HOURS_PER_PERSON_YEAR, shut.HOURS_PER_PERSON_YEAR)
