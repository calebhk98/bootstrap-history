"""A home stratum's income is the earnings of the household cohorts in its slice of the population, not members x work
share x pay; before the economy has opened (it answers nothing yet) the wage bridge stays. Complaint 640: the slice, the
mapping and the view's answers are called on strata and cohort curves built here. The strata's books over a year (income
credited, the keep of the bonded, money conserved) are test_agents_strata, and the rank tie-break is test_stratum_rank_ties."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.agents import stratum_year
from sim.agents.api import Stratum, observed_incomes, stratum_id
from sim.agents.records import ActorRecord
from sim.agents.strata_observed import slice_income
from sim.engine.agents_port_cast import CastView

from .agents_fake_world import FakeWorld

PAY = {"labourer": 100.0, "artisan": 400.0}
WORK_SHARE = 0.5


class PayWorld(FakeWorld):
    """Pays each trade a flat yearly figure, and answers no cohort curve (the economy is opening)."""

    def pay_per_person_year(self, trade):
        return PAY[trade]

    def observed_stratum(self, country, name):
        return None

    def society_output(self):
        return 1.0e6

    def subsistence_cost_per_person_year(self):
        return 10.0

    def need_floor_costs_per_person_year(self):
        return {"food": 10.0}


def stratum(name, members, trade=None, bonded=False, owner=None):
    plan = {"work_share": WORK_SHARE, "bonded": bonded}
    if trade:
        plan["trade"] = trade
    if owner:
        plan["owner"] = owner
    return Stratum(stratum_id("home", name), ActorRecord(kind="stratum", stratum=name, members=members, plan=plan))


# ---- slices of a curve ----------------------------------------------------------------------
rows = [(10.0, 10.0), (10.0, 40.0), (20.0, 200.0)]
check("the whole curve is every cohort's income", abs(slice_income(rows, 0.0, 40.0) - 250.0) < 1e-9)
check("a slice inside one row takes its share", abs(slice_income(rows, 15.0, 20.0) - 20.0) < 1e-9)
check("a slice across rows adds the parts", abs(slice_income(rows, 5.0, 25.0) - (5.0 + 40.0 + 50.0)) < 1e-9)
check("a slice past the end of the curve earns nothing", slice_income(rows, 40.0, 50.0) == 0.0)

# ---- before the economy has opened: the wage bridge stays -----------------------------------------------
class OpeningSim:
    """A game whose economy answers no cohort curve."""

    def __init__(self, strata):
        self.economy = SimpleNamespace(agent_cohort_incomes=lambda: None)
        self.actors = SimpleNamespace(of_kind=lambda kind: strata)


class View(CastView):
    def __init__(self, sim):
        self._sim = sim

    def pay_per_person_year(self, trade):
        return PAY[trade]

    def society_output(self):
        return 1.0e6


toilers, artisans = stratum("toilers", 8000.0, "labourer"), stratum("artisans", 2000.0, "artisan")
check("before the economy has opened strata observe nothing", View(OpeningSim([toilers, artisans])).observed_stratum(None, "toilers") is None)
bridge = PayWorld()
before = toilers.money
stratum_year.run_year(toilers, bridge)
check("before the economy has opened the strata still earn by the bridge: members x work share x pay",
      abs(toilers.record.income.get("edge:economy", 0.0) - 8000.0 * WORK_SHARE * PAY["labourer"]) < 1e-6, toilers.record.income)

# ---- the economy open ------------------------------------------------------------------------------
curve = [(2000.0, 1.0e5), (3000.0, 6.0e5), (5000.0, 5.0e6)]   # poorest per head first
check("the fixture curve runs poorest per head first", all(a[1] / a[0] <= b[1] / b[0] for a, b in zip(curve, curve[1:])))
strata = [toilers, artisans]
incomes = observed_incomes(strata, bridge, curve)
check("every home stratum is mapped to a slice", set(incomes) == {"toilers", "artisans"}, incomes)
cohort_total = sum(income for _people, income in curve)
cohort_people = sum(people for people, _income in curve)
members = sum(actor.record.members for actor in strata)
check("the strata's incomes add up to the cohorts' (scaled to the strata's people)",
      abs(sum(incomes.values()) - cohort_total * members / cohort_people) <= 1e-6 * cohort_total, (sum(incomes.values()), cohort_total))
check("the stratum that would earn less per head takes the poorer slice", incomes["toilers"] / 8000.0 < incomes["artisans"] / 2000.0, incomes)
check("no curve gives no incomes", observed_incomes(strata, bridge, []) == {})

open_sim = SimpleNamespace(economy=SimpleNamespace(agent_cohort_incomes=lambda: curve),
                           actors=SimpleNamespace(of_kind=lambda kind: strata))
view = View(open_sim)
check("the world answers a stratum's income from the mapping, once the economy runs",
      all(abs(view.observed_stratum(None, name)["income"] - income) <= 1e-6 * max(1.0, income) for name, income in incomes.items()))
check("another country's strata are not the home cohorts", view.observed_stratum("elsewhere", "toilers") is None)
check("a stratum that is not in the roster has no slice", view.observed_stratum(None, "nobody") is None)
exited = stratum("gone", 500.0, "labourer")
exited.record.exited_year = 5
roster = SimpleNamespace(economy=open_sim.economy, actors=SimpleNamespace(of_kind=lambda kind: strata + [exited]))
check("a stratum that exited takes no slice", View(roster).observed_stratum(None, "gone") is None)

# ---- the economy offers its cohorts poorest per head first, the home country's only ------------------------
from sim.economy import api as economy_api


def cohort(agent_id, tile, people, income):
    return SimpleNamespace(agent_id=agent_id, tile=tile, people=people, last_year_income=income)


cohorts = {entry.agent_id: entry for entry in (cohort("b", "home1", 10.0, 500.0), cohort("a", "home1", 10.0, 500.0),
                                               cohort("c", "home2", 40.0, 100.0), cohort("rich", "home2", 5.0, 5000.0),
                                               cohort("empty", "home1", 0.0, 0.0), cohort("far", "away", 100.0, 1.0))}
setup = SimpleNamespace(tiles=("home1", "home2", "away"), civ_id="rome", countries=lambda: ["rome", "han"],
                        tiles_of=lambda country: ("home1", "home2") if country == "rome" else ("away",))
shared = SimpleNamespace(setup=setup, record=SimpleNamespace(cohorts=cohorts))
offered = economy_api.cohort_incomes(shared)
check("the curve runs poorest per head first", all(a[1] / a[0] <= b[1] / b[0] for a, b in zip(offered, offered[1:])), offered)
check("cohorts earning the same per head keep the order of their people, so the curve is stable",
      offered == [(40.0, 100.0), (10.0, 500.0), (10.0, 500.0), (5.0, 5000.0)], offered)
check("a cohort of another country or of nobody is left out", sum(people for people, _income in offered) == 65.0, offered)
check("the curve of the other country is its own", economy_api.cohort_incomes(shared, "han") == [(100.0, 1.0)])
