"""WIRING TWO (Complaints/closed/46-one-weather-draw-for-a-continent.md): the weather is drawn per land cell of the
civilisation's own territory and pooled by cultivable-land share, and the seed of a draw is a pure function of
(civilisation, cell, year, the game's weather salt). Each rule is called on the real method over a stand-in holding a
civilisation's data, a salt and a dice (no game is built). Determinism across two games and a save is
test_regional_weather_wiring_scenario; the century bar is test_regional_weather_century_validation."""
import collections
import random
import statistics
from types import SimpleNamespace

from .harness import check

from sim import simulator
from sim.engine import data
from sim.engine.core import Sim
from sim.geography import api as geography_api
from sim.world import agriculture
from sim.world.weather_pooling import correlation_cholesky, pooled_multiplier

QUICK_TOPIC = True

ROME = simulator.load_civ("rome_100ad")


def _stub(civ, salt=0, seed=1):
    """What the weather rules read of a game: the civilisation, its map, the weather salt and the game's dice."""
    stub = SimpleNamespace(civ=civ, world_map=None, rng=random.Random(seed),
                           state=SimpleNamespace(scenario=SimpleNamespace(weather_salt=salt)))
    stub._cap_pooled_farm_weather_cells = lambda cells: Sim._cap_pooled_farm_weather_cells(stub, cells)
    return stub


# --- the cells and their weights
cells = Sim._compute_farm_weather_cells(_stub(ROME))
home_regions = set(geography_api.regions_of_tiles(geography_api.tiles_held(ROME)))
tiles = data.load_geography()["land_tiles"]["tiles"]
check("the weights are shares of the territory's cultivable land: they sum to one",
      abs(sum(cell.weight for cell in cells) - 1.0) < 1e-9, sum(cell.weight for cell in cells))
check("every cell sits in a region the civilisation holds, and the territory breaks into more cells than regions",
      all(tiles[cell.cell_id]["old_region"] in home_regions for cell in cells) and len(cells) > len(home_regions), (len(cells), len(home_regions)))
check("the weighting is by land, not by counting: a desert cell and a fertile one weigh differently",
      max(cell.weight for cell in cells) > min(cell.weight for cell in cells))
check("a civilisation with no territory has no cells", Sim._compute_farm_weather_cells(_stub(dict(ROME, home_regions=[], home_tiles=[]))) == [])
check("cells are the same every time they are derived",
      Sim._compute_farm_weather_cells(_stub(ROME)) == cells)

# --- the pooled multiplier: steadier than one draw, and centred on a normal year
lower = correlation_cholesky(cells, 800.0)
generator = random.Random(7)
pooled = [pooled_multiplier(cells, lower, [generator.gauss(0.0, 1.0) for _ in cells],
                            agriculture.WEATHER_YIELD_STDEV_FRACTION, agriculture.WEATHER_FLOOR_MULTIPLIER,
                            agriculture.WEATHER_CEILING_MULTIPLIER) for _ in range(1000)]
check("pooling a territory's cells reduces the spread of the harvest multiplier well below a single draw's, yet not to zero",
      0.03 < statistics.pstdev(pooled) < agriculture.WEATHER_YIELD_STDEV_FRACTION * 0.6, statistics.pstdev(pooled))
check("the pooled multiplier averages close to one", abs(statistics.fmean(pooled) - 1.0) < 0.02, statistics.fmean(pooled))

# --- the seed is a pure function of (civilisation, region, year, salt)
first, second = _stub(ROME, salt=424242), _stub(ROME, salt=424242, seed=99)
check("the same inputs always give the same seed, whatever the dice",
      Sim._farm_year_weather_seed(first, 150, region="italia") == Sim._farm_year_weather_seed(second, 150, region="italia"))
seeds = {Sim._farm_year_weather_seed(first, 150, region=region) for region in sorted(home_regions)}
check("different regions give different seeds", len(seeds) == len(home_regions), seeds)
check("different years give different seeds",
      len({Sim._farm_year_weather_seed(first, year, region="italia") for year in range(100, 130)}) == 30)
civ_component = sum((index + 1) * ord(character) for index, character in enumerate(str(ROME.get("id", "civ"))))
check("omitting the region mixes in no region ingredient: the seed is the civilisation, year and salt only",
      Sim._farm_year_weather_seed(first, 150) == (civ_component * 1000003 + 150 * 97 + 424242 * 104729) % (2 ** 32))
check("two civilisations sharing a region name still draw different weather for it",
      Sim._farm_year_weather_seed(first, 150, region="italia")
      != Sim._farm_year_weather_seed(_stub(dict(ROME, id="some_other_civ"), salt=424242), 150, region="italia"))
check("a different salt gives a different seed, so each game has its own weather",
      Sim._farm_year_weather_seed(first, 150, region="italia")
      != Sim._farm_year_weather_seed(_stub(ROME, salt=424243), 150, region="italia"))
unsalted = _stub(ROME, salt=0, seed=5)
drawn = Sim._farm_year_weather_seed(unsalted, 150, region="italia")
check("a game with no salt draws one from its dice, keeps it, and then seeds the same way every time",
      unsalted.state.scenario.weather_salt > 0 and Sim._farm_year_weather_seed(unsalted, 150, region="italia") == drawn)
check("...and another game's dice give another salt",
      _stub(ROME, salt=0, seed=6).state.scenario.weather_salt == 0
      and Sim._farm_year_weather_seed(_stub(ROME, salt=0, seed=6), 150, region="italia") != drawn)
