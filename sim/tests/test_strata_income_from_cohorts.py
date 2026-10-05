"""With the agent economy on, a home stratum's income is the earnings of the household cohorts in its slice of the
population, not members x work share x pay; with it off the wage bridge stays. Money is conserved."""
import random

from .harness import *  # noqa: F401,F403

from sim.agents import stratum_year
from sim.agents.api import observed_incomes
from sim.agents.strata_observed import slice_income
from sim.engine.agents_port import SimWorld


def rome_game(agent_economy):
    game = S.Sim(NODES, list(ORDER), random.Random(1), events=False, manual=True, civ=S.load_civ("rome_100ad"),
                 cfg={"agent_economy": agent_economy})
    for _ in range(2):  # the first year only seeds the roster
        game.state.scenario.year += 1
        game.advance_actors(game.state.scenario.year)
    return game


def home(game):
    return [actor for actor in game.actors.of_kind("stratum") if actor.record.country is None]


def edge_in(actors):
    return sum(actor.record.income.get("edge:economy", 0.0) for actor in actors)


# ---- slices of a curve ----------------------------------------------------------------------
rows = [(10.0, 10.0), (10.0, 40.0), (20.0, 200.0)]
check("the whole curve is every cohort's income", abs(slice_income(rows, 0.0, 40.0) - 250.0) < 1e-9)
check("a slice inside one row takes its share", abs(slice_income(rows, 15.0, 20.0) - 20.0) < 1e-9)
check("a slice across rows adds the parts", abs(slice_income(rows, 5.0, 25.0) - (5.0 + 40.0 + 50.0)) < 1e-9)

# ---- agent economy off: the wage bridge stays -----------------------------------------------
off = rome_game(False)
check("with the economy off no cohort curve is offered", off.economy.agent_cohort_incomes() is None)
check("with the economy off strata observe nothing", SimWorld(off).observed_stratum(None, "labourers") is None)
check("with the economy off the strata still earn by the bridge", edge_in(home(off)) > 0.0)

# ---- agent economy on -----------------------------------------------------------------------
on = rome_game(True)
curve = on.economy.agent_cohort_incomes()
check("the agent economy offers its cohorts' incomes", bool(curve) and all(people > 0.0 for people, _ in curve))
check("the curve runs poorest per head first",
      all(a[1] / a[0] <= b[1] / b[0] + 1e-9 for a, b in zip(curve, curve[1:])))
strata = home(on)
world = SimWorld(on)
incomes = observed_incomes(strata, world, curve)
check("every home stratum is mapped to a slice", set(incomes) == {actor.record.stratum for actor in strata}, incomes)
cohort_total = sum(income for _people, income in curve)
cohort_people = sum(people for people, _income in curve)
members = sum(actor.record.members for actor in strata)
check("the strata's incomes add up to the cohorts' (scaled to the strata's people)",
      abs(sum(incomes.values()) - cohort_total * members / cohort_people) <= 1e-6 * max(1.0, cohort_total),
      (sum(incomes.values()), cohort_total))
check("the world answers a stratum's income from the mapping, once the economy runs",
      all(abs(world.observed_stratum(None, name)["income"] - income) <= 1e-6 * max(1.0, income)
          for name, income in incomes.items()))
check("another country's strata are not the home cohorts", world.observed_stratum("elsewhere", "labourers") is None)

print("Rome, stratum income: cohort-mapped vs the wage bridge (agent economy on):")
for actor in sorted(strata, key=lambda actor: actor.record.stratum):
    bridge = stratum_year.bonded_product(actor, world) if actor.is_bonded() else stratum_year.own_income(actor, world)
    print("  %-10s members %10.0f  cohorts %14.0f  bridge %14.0f" % (
        actor.record.stratum, actor.record.members, incomes[actor.record.stratum], bridge))

# ---- the books after a year: income is the mapped cohort income ------------------------------
before = {actor.actor_id: actor.record.income.get("edge:economy", 0.0) for actor in home(on)}
expected = observed_incomes(home(on), SimWorld(on), on.economy.agent_cohort_incomes())
on.state.scenario.year += 1
on.advance_actors(on.state.scenario.year)
for actor in home(on):
    credited = actor.record.income.get("edge:economy", 0.0) - before[actor.actor_id]
    if actor.is_bonded():
        check("the bonded earn nothing of their own", credited <= 1e-9, credited)
        keeper = on.actors.actors[actor.neighbour_id(actor.record.plan["owner"])]
        check("the bonded stratum keeps a labour product for its keeper to be credited", keeper.record.income.get("edge:economy", 0.0) > 0.0)
        continue
    check("%s is credited about its mapped cohort income" % actor.record.stratum,
          credited > 0.0 and abs(credited - expected[actor.record.stratum]) <= 0.25 * expected[actor.record.stratum],
          (credited, expected[actor.record.stratum]))


def edge_net(actors):
    """Money in less money out across the edge of the strata, counting the state's relief as coming in."""
    return sum(sum(v for k, v in a.record.income.items() if k.startswith("edge:") or k == "relief")
               - sum(v for k, v in a.record.outlays.items() if k.startswith("edge:")) for a in actors)


all_strata = on.actors.of_kind("stratum")
money_before, edge_before = sum(a.money for a in all_strata), edge_net(all_strata)
on.state.scenario.year += 1
on.advance_actors(on.state.scenario.year)
all_strata = on.actors.of_kind("stratum")
check("strata money changes only by what crossed the edge and the state's relief (moves, keep and allowances net to zero)",
      abs((sum(a.money for a in all_strata) - money_before) - (edge_net(all_strata) - edge_before))
      <= 1e-6 * max(1.0, abs(money_before)), (sum(a.money for a in all_strata) - money_before, edge_net(all_strata) - edge_before))
