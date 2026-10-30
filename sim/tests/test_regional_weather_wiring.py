"""WIRING TWO (Complaints/closed/46-one-weather-draw-for-a-continent.md): the weather is drawn per land cell of the
civilisation's own territory and pooled by cultivable-land share, and the seed of a draw is a pure function of
(civilisation, cell, year, the game's weather salt). Each rule is called as a plain function, or on the agriculture
module built over plain values (no game is built). Determinism across two games and a save is
test_weather_multiplier_ignores_dice; the century bar (population above its start) is `python3 sim/simulator.py baseline-ensemble`."""
import random
import statistics
from types import SimpleNamespace

from .harness import check

from sim import simulator
from sim.agriculture import rules
from sim.agriculture.constants import FARM_WEATHER_POOLED_CELL_CAP
from sim.engine import data
from sim.tests import land_host
from sim.geography import api as geography_api
from sim.tests import agriculture_stand_in
from sim.world import agriculture
from sim.world.weather_pooling import correlation_cholesky, pooled_multiplier

QUICK_TOPIC = True

ROME = simulator.load_civ("rome_100ad")


def _cells(civ):
    """The pooled cells over the tiles a civilisation holds."""
    rows = land_host.build(civ).held_tile_geometry()
    return rules.pooled_cells(rules.raw_cells(rows), FARM_WEATHER_POOLED_CELL_CAP)


def _seed(civ, year, region=None, salt=424242):
    return rules.weather_seed(civ.get("id", "civ"), region, year, salt)


# --- the cells and their weights
cells = _cells(ROME)
home_regions = set(geography_api.regions_of_tiles(geography_api.tiles_held(ROME)))
tiles = data.load_geography()["land_tiles"]["tiles"]
check("the weights are shares of the territory's cultivable land: they sum to one",
      abs(sum(cell.weight for cell in cells) - 1.0) < 1e-9, sum(cell.weight for cell in cells))
check("every cell sits in a region the civilisation holds, and the territory breaks into more cells than regions",
      all(tiles[cell.cell_id]["old_region"] in home_regions for cell in cells) and len(cells) > len(home_regions), (len(cells), len(home_regions)))
check("the weighting is by land, not by counting: a desert cell and a fertile one weigh differently",
      max(cell.weight for cell in cells) > min(cell.weight for cell in cells))
check("a civilisation with no territory has no cells", _cells(dict(ROME, home_regions=[], home_tiles=[])) == [])
check("cells are the same every time they are derived",
      _cells(ROME) == cells)

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
check("the same inputs always give the same seed", _seed(ROME, 150, "italia") == _seed(ROME, 150, "italia"))
seeds = {_seed(ROME, 150, region) for region in sorted(home_regions)}
check("different regions give different seeds", len(seeds) == len(home_regions), seeds)
check("different years give different seeds", len({_seed(ROME, year, "italia") for year in range(100, 130)}) == 30)
civ_component = sum((index + 1) * ord(character) for index, character in enumerate(str(ROME.get("id", "civ"))))
check("omitting the region mixes in no region ingredient: the seed is the civilisation, year and salt only",
      _seed(ROME, 150) == (civ_component * 1000003 + 150 * 97 + 424242 * 104729) % (2 ** 32))
check("two civilisations sharing a region name still draw different weather for it",
      _seed(ROME, 150, "italia") != _seed(dict(ROME, id="some_other_civ"), 150, "italia"))
check("a different salt gives a different seed, so each game has its own weather",
      _seed(ROME, 150, "italia") != _seed(ROME, 150, "italia", salt=424243))
unsalted = agriculture_stand_in.build(salt=0, dice_seed=5, civ_id=ROME["id"])
drawn = unsalted.weather_seed(150, "italia")
check("a game with no salt draws one from its dice, keeps it, and then seeds the same way every time",
      unsalted.world.weather_salt > 0 and unsalted.weather_seed(150, "italia") == drawn)
check("...and another game's dice give another salt",
      agriculture_stand_in.build(salt=0, dice_seed=6, civ_id=ROME["id"]).weather_seed(150, "italia") != drawn)
