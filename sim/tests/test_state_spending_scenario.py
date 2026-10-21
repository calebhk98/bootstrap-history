"""SCENARIO: a state's standing lines, the army its hazards want, revenue, patron funding and surplus on a real game.
Complaints 286 and 287: a state keeps up more than an army and officials (roads, public buildings,
a court, a dole, a navy), each priced from a physical stock; the army it wants follows the threat the
civilisation's own hazards describe; soldiers are out of production; and patron funding is paid out of
the treasury."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.agents import budget, government_levers, order
from sim.agents.purses import DEPOSIT_LOST
from sim.engine.coin_hoard import KEEPING_CAUSE
from sim.engine.theft_charge import THEFT_CAUSE
from sim.geography import api as geography_api, territory


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def lines_of(game):
    return {line.name: line for line in budget.standing_lines(SimWorld(game))}


# ---- the standing need names every line a state cannot skip -------------------------------------
game = unopened_sim()
lines = lines_of(game)
check("a coastal state with cities keeps an army, officials, roads, public buildings, a court, a dole and a navy",
      {"army", "administration", "roads", "public_buildings", "court", "dole", "navy"} <= set(lines), sorted(lines))
check("and no line the budget does not name (the lever-named lines, the works, the order staff, a campaign and a donative)",
      set(lines) <= set(government_levers.budget_line_names()) | set(order.STAFF_LINES), sorted(lines))
check("every line is priced from people at wages or goods at the market's price",
      all(line.money > 0.0 for line in lines.values()), {name: line.money for name, line in lines.items()})
check("the navy is manned by sailors, the dole is grain, public buildings are masons' work",
      "sailor" in lines["navy"].labour and lines["dole"].materials and "mason" in lines["public_buildings"].labour,
      (lines["navy"].labour, lines["dole"].materials, lines["public_buildings"].labour))
pristine_civ = copy.deepcopy(game.civ)   # the one game below is shared; each check restores what it changed
pristine_population = {cohort: getattr(game.population, cohort) for cohort in ("children", "working_age", "elderly")}
landlocked = game
landlocked.civ.pop("home_tiles", None)
landlocked.civ["home_regions"] = ["levant_mesopotamia"]
dry = lines_of(landlocked)
check("a state's roads follow the tiles it holds",
      "roads" in dry and dry["roads"].money != lines["roads"].money, (dry.get("roads"), lines["roads"].money))
inland = game
inland.civ.pop("home_tiles", None)
inland.civ["home_regions"] = []
check("a state with no territory keeps no roads and no navy",
      not {"roads", "navy"} & set(lines_of(inland)), sorted(lines_of(inland)))
game.civ = copy.deepcopy(pristine_civ)
bigger_city = game
for cohort in ("children", "working_age", "elderly"):
    setattr(bigger_city.population, cohort, getattr(bigger_city.population, cohort) * 2.0)
check("a larger population keeps up more public buildings and feeds more of its poor",
      lines_of(bigger_city)["public_buildings"].money > 1.5 * lines["public_buildings"].money
      and lines_of(bigger_city)["dole"].money > 1.5 * lines["dole"].money)
check("the garrison does not grow with the people: it follows the frontier and the threat",
      abs(lines_of(bigger_city)["army"].labour["soldier"] - lines["army"].labour["soldier"]) < 1e-6)
for cohort, people in pristine_population.items():
    setattr(game.population, cohort, people)

# ---- the army the state wants follows the threat its hazards describe ---------------------------
opening_year = game.state.scenario.year
game.state.scenario.year = 120
army_in_calm = SimWorld(game).army_wanted()
game.state.scenario.year = 240
army_in_crisis = SimWorld(game).army_wanted()
game.state.scenario.year = opening_year
check("in the opening year the state wants the civilisation's opening force",
      abs(army_in_calm - game.civ["standing_army"]) < 1e-6 * game.civ["standing_army"],
      (army_in_calm, game.civ["standing_army"]))
check("while the civilisation's own hazards threaten a sack the state wants a bigger army",
      army_in_crisis > 1.2 * army_in_calm, (army_in_crisis, army_in_calm))

# ---- soldiers are out of production -------------------------------------------------------------
game.state_treasury().record.army = 0.0
revenue_without_army = SimWorld(game).state_revenue()
game.state_treasury().record.army = 1.0e6
revenue_with_army = SimWorld(game).state_revenue()
check("soldiers kept under arms owe no poll tax, so the people it is assessed on and the state's revenue are smaller",
      revenue_with_army < revenue_without_army, (revenue_with_army, revenue_without_army))

# ---- patron funding is a payment out of the treasury --------------------------------------------
patron = unopened_sim()
patron.running_with_mechanic = lambda name: [name]
check("before the treasury has paid anything the founder has no patron funding", patron.state_funding() == 0.0)
ask = patron.patron_funding_ask()
check("what a patron would give is a formula (a labelled heuristic), no longer income by itself", ask > 0.0, ask)
rich = patron
rich.running_with_mechanic = lambda name: [name]
rich_treasury = rich.state_treasury()
rich_treasury.money = 1.0e15
one_year(rich)
check("a state with a purse pays the founder what the patron asks, out of its reserve",
      abs(rich.state_funding() - rich.patron_funding_ask()) < 1e-6 * ask
      and abs(rich_treasury.record.outlays.get("patronage", 0.0) - rich.state_funding()) < 1e-6 * ask,
      (rich.state_funding(), rich_treasury.record.outlays))
poor = unopened_sim()
poor.running_with_mechanic = lambda name: [name]
poor.civ["standing_army"] = 1.0e8
poor.state_treasury().money = 0.0
one_year(poor)
check("a state in deficit, with its standing need unpaid, funds nobody",
      poor.state_funding() == 0.0 and poor.state_treasury().record.outlays.get("patronage", 0.0) == 0.0,
      (poor.state_funding(), poor.state_treasury().record.outlays))
check("the founder's revenue includes only what the treasury paid",
      poor.revenue() <= rich.revenue() and rich.revenue() > 0.0, (poor.revenue(), rich.revenue()))

# ---- a surplus is not hoarded for ever, so a later collapse is felt -----------------------------
hoard = unopened_sim()
hoard_treasury = hoard.state_treasury()
hoard_treasury.money = 1.0e18
one_year(hoard)
check("reserve beyond what the state holds against risk buys named works it lacks, never an outlay that pays no one",
      "works" not in hoard_treasury.record.outlays and "discretionary" not in hoard_treasury.record.outlays
      and all(purpose in hoard_treasury.record.need or purpose.startswith("building ") or purpose in
              {"interest", "patronage", "relief", DEPOSIT_LOST, KEEPING_CAUSE, THEFT_CAUSE}   # theft goes to the thieves edge
              for purpose in hoard_treasury.record.outlays),
      hoard_treasury.record.outlays)
check("the purse still equals income less outlays after the works",
      abs(hoard_treasury.money - (1.0e18 + sum(hoard_treasury.record.income.values())
                                  - sum(hoard_treasury.record.outlays.values()))) < 1e-6 * 1.0e18, hoard_treasury.money)
collapse = unopened_sim()
collapse_record = collapse.state_treasury().record
collapse_record.revenue_forms = [form for form in collapse_record.revenue_forms if form["basis"] == "harvest"]   # the state's own forms, copied from the file at setup
collapse.state.holdings.farm_last_harvest_kg = 1.0  # what the farms yield all but stops
for _year in range(8):
    one_year(collapse)
check("when revenue collapses the reserve lasts a few years, then the state goes short and seeks it of the taxpayers it sees",
      sum(collapse.state_treasury().record.unfunded.values()) > 0.0, collapse.state_treasury().record.unfunded)
