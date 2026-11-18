"""Why the opening places a recipe where it does: whether it is sited, which of its inputs only fixed sites supply (it is then
placed beside them), on how many tiles a run pays at the opening's prices and wages, how many market areas its main output has
and how many of them hold a tile it may be placed on, and the tiles its makers stand on with their share of the runs.
Usage: python3 placement_why_probe.py <civ> <recipe> [<recipe> ...]"""
import random, sys
from collections import defaultdict
from sim.economy import api as economy_api, location, location_inputs, sites
from sim.economy.producers import paying_output
from sim.engine.ui_port import Sim, load, load_civ

civ, recipes = sys.argv[1], sys.argv[2:]
_t, _p, nodes, _w, _g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup)
economy_api.begin_spin_up(economy)
record, area_map = economy.record, economy.area_map
by_limits = sites.limits_by_recipe(setup.site_limits)
incumbents = defaultdict(list)
for producer in record.producers.values():
    incumbents[producer.recipe_id].append(producer)
for recipe_id in recipes:
    recipe = setup.recipes[recipe_id]
    main = paying_output(recipe, setup.opening_prices)
    areas = area_map.areas(main) if main in area_map.goods() else ()
    placed = location._placed_tiles(setup, recipe)
    every = sites.suited_tiles(recipe, setup.tiles, sorted(setup.tiles), setup.recipe_allowed)
    with_tile = [area for area in areas if any(tile in placed for tile in area.tiles)]
    makers = defaultdict(float)
    for producer in incumbents.get(recipe_id, ()):
        makers[producer.tile] += producer.expected_sales
    total = sum(makers.values()) or 1.0
    people = setup.opening_population_by_tile
    print("%s (main output %s): sited %s; suited tiles %d; tiles where a run pays at the opening's prices and wages %d; "
          "areas of the output %d, of which %d hold such a tile (they hold %.2f of the people)" % (
              recipe_id, main, sites.is_sited(recipe, by_limits), len(every), len(placed), len(areas), len(with_tile),
              sum(people.get(tile, 0.0) for area in with_tile for tile in area.tiles) / (sum(people.values()) or 1.0)))
    try:
        fixed = location_inputs.fixed_inputs(recipe, record.producers, setup.recipes, by_limits)
    except Exception as error:      # the reads of the placement differ from the record's store
        fixed = "could not be read here (%s)" % type(error).__name__
    print("   inputs only fixed sites supply: %s" % (fixed or "none"))
    print("   makers on %d tiles: %s" % (len(makers), ", ".join("%s %.2f" % (tile, runs / total) for tile, runs in sorted(makers.items(), key=lambda item: -item[1])[:8])))
