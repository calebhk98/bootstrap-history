"""Complaints 300 and 301: a state keeps up more than an army and officials (roads, public buildings,
a court, a dole, a navy), each priced from a physical stock; the army it wants follows the threat the
civilisation's own hazards describe; soldiers are out of production; and patron funding is paid out of
the treasury."""
from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld
from sim.engine.actors import budget
from sim.world import territory


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def lines_of(game):
    return {line.name: line for line in budget.standing_lines(SimWorld(game))}


# ---- the map gives a state its frontier, its coast and its roads ---------------------------------
held = territory.holdings(["italia", "gaul_germania"])
check("a territory has a frontier, a coast and an internal road network, all in km",
      held.frontier_km > 0.0 and held.coast_km > 0.0 and held.road_km > 0.0, held)
bigger = territory.holdings(["italia", "gaul_germania", "britannia", "hispania"])
check("holding more tiles means more road to keep up",
      bigger.road_km > held.road_km, (bigger.road_km, held.road_km))
alone = territory.holdings(["italia"])
check("a state's road is the links between its own tiles, so an empty territory has none",
      territory.holdings([]).road_km == 0.0 and territory.holdings([]).frontier_km == 0.0
      and alone.road_km < held.road_km, alone)

# ---- the standing need names every line a state cannot skip -------------------------------------
game = sim()
lines = lines_of(game)
check("a coastal state with cities keeps an army, officials, roads, public buildings, a court, a dole and a navy",
      set(lines) == {"army", "administration", "roads", "public_buildings", "court", "dole", "navy"},
      sorted(lines))
check("every line is priced from people at wages or goods at the market's price",
      all(line.money > 0.0 for line in lines.values()), {name: line.money for name, line in lines.items()})
check("the navy is manned by sailors, the dole is grain, public buildings are masons' work",
      "sailor" in lines["navy"].labour and lines["dole"].materials and "mason" in lines["public_buildings"].labour,
      (lines["navy"].labour, lines["dole"].materials, lines["public_buildings"].labour))
landlocked = sim(civ="rome_100ad")
landlocked.civ["home_regions"] = ["levant_mesopotamia"]
dry = lines_of(landlocked)
check("a state's roads follow the tiles it holds",
      "roads" in dry and dry["roads"].money != lines["roads"].money, (dry.get("roads"), lines["roads"].money))
inland = sim()
inland.civ["home_regions"] = []
check("a state with no territory keeps no roads and no navy",
      not {"roads", "navy"} & set(lines_of(inland)), sorted(lines_of(inland)))
bigger_city = sim()
for cohort in ("children", "working_age", "elderly"):
    setattr(bigger_city.population, cohort, getattr(bigger_city.population, cohort) * 2.0)
check("a larger population keeps up more public buildings and feeds more of its poor",
      lines_of(bigger_city)["public_buildings"].money > 1.5 * lines["public_buildings"].money
      and lines_of(bigger_city)["dole"].money > 1.5 * lines["dole"].money)
check("the garrison does not grow with the people: it follows the frontier and the threat",
      abs(lines_of(bigger_city)["army"].labour["labourer"] - lines["army"].labour["labourer"]) < 1e-6)

# ---- the army the state wants follows the threat its hazards describe ---------------------------
calm = sim()
calm.state.scenario.year = 120
crisis = sim()
crisis.state.scenario.year = 240
check("in the opening year the state wants the civilisation's opening force",
      abs(SimWorld(calm).army_wanted() - calm.civ["standing_army"]) < 1e-6 * calm.civ["standing_army"],
      (SimWorld(calm).army_wanted(), calm.civ["standing_army"]))
check("while the civilisation's own hazards threaten a sack the state wants a bigger army",
      SimWorld(crisis).army_wanted() > 1.2 * SimWorld(calm).army_wanted(),
      (SimWorld(crisis).army_wanted(), SimWorld(calm).army_wanted()))
check("a hazard that does not threaten a sack leaves the army alone",
      abs(SimWorld(sim(civ="norse_900ad")).army_wanted() - sim(civ="norse_900ad").civ["standing_army"]) < 1e-6)

# ---- soldiers are out of production -------------------------------------------------------------
free = sim()
free.state_treasury().record.army = 0.0
drawn = sim()
drawn.state_treasury().record.army = 1.0e6
check("soldiers kept under arms are not producing, so society's output and the state's revenue are smaller",
      SimWorld(drawn).society_output() < SimWorld(free).society_output()
      and SimWorld(drawn).state_revenue() < SimWorld(free).state_revenue(),
      (SimWorld(drawn).society_output(), SimWorld(free).society_output()))
slump = sim()
slump.state.economy.output_factor = 0.5
check("a crisis that cuts what the economy makes cuts what the state can take",
      SimWorld(slump).state_revenue() < 0.6 * SimWorld(sim()).state_revenue(),
      (SimWorld(slump).state_revenue(), SimWorld(sim()).state_revenue()))

# ---- patron funding is a payment out of the treasury --------------------------------------------
patron = sim()
patron.running_with_mechanic = lambda name: [name]
check("before the treasury has paid anything the founder has no patron funding", patron.state_funding() == 0.0)
ask = patron.patron_funding_ask()
check("what a patron would give is a formula (a labelled heuristic), no longer income by itself", ask > 0.0, ask)
rich = sim()
rich.running_with_mechanic = lambda name: [name]
rich_treasury = rich.state_treasury()
rich_treasury.money = 1.0e15
one_year(rich)
check("a state with a purse pays the founder what the patron asks, out of its reserve",
      abs(rich.state_funding() - rich.patron_funding_ask()) < 1e-6 * ask
      and abs(rich_treasury.record.outlays.get("patronage", 0.0) - rich.state_funding()) < 1e-6 * ask,
      (rich.state_funding(), rich_treasury.record.outlays))
poor = sim()
poor.running_with_mechanic = lambda name: [name]
poor.civ["standing_army"] = 1.0e8
poor.state_treasury().money = 0.0
one_year(poor)
check("a state in deficit, with its standing need unpaid, funds nobody",
      poor.state_funding() == 0.0 and poor.state_treasury().record.outlays.get("patronage", 0.0) == 0.0,
      (poor.state_funding(), poor.state_treasury().record.outlays))
check("the founder's revenue includes only what the treasury paid",
      poor.revenue() <= rich.revenue() and rich.revenue() > 0.0, (poor.revenue(), rich.revenue()))
