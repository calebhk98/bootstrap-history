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
pristine_civ = copy.deepcopy(game.civ)   # the one game below is shared; each check restores what it changed
pristine_population = {cohort: getattr(game.population, cohort) for cohort in ("children", "working_age", "elderly")}


def with_tiles_released(count):
    """A game whose home country has given `count` of its tiles to another country (all when None): territory is the
    owner map's (`transfer_tile`), not the civilisation file's, once a game is running. They are given away, not released,
    because a map with no owner at all is seeded afresh from the files."""
    fresh = unopened_sim()
    home = str(fresh.civ["id"])
    held = fresh.tiles_owned_by(home)
    for tile_id in held if count is None else held[:count]:
        fresh.transfer_tile(tile_id, "another_country", cause="test")
    return fresh


partly_lost = lines_of(with_tiles_released(len(game.tiles_owned_by(str(game.civ["id"]))) // 2))
check("a state's roads follow the tiles it holds",
      partly_lost.get("roads") is not None and partly_lost["roads"].money != lines["roads"].money, (partly_lost.get("roads"), lines["roads"].money))
check("a state with no territory keeps no roads and no navy",
      not {"roads", "navy"} & set(lines_of(with_tiles_released(None))), sorted(lines_of(with_tiles_released(None))))
game.civ = copy.deepcopy(pristine_civ)
bigger_city = game
for cohort in ("children", "working_age", "elderly"):
    setattr(bigger_city.population, cohort, getattr(bigger_city.population, cohort) * 2.0)
check("the garrison does not grow with the people: it follows the frontier and the threat",
      abs(lines_of(bigger_city)["army"].labour["soldier"] - lines["army"].labour["soldier"]) < 1e-6)
for cohort, people in pristine_population.items():
    setattr(game.population, cohort, people)

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
