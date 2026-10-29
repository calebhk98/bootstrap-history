"""The agriculture module built for a test, with plain values for the views it reads (sim/tests/module_harness.py).

    farm = agriculture_stand_in.build(rows=[("t1", 40.0, 10.0, 1000.0, 0.5)], salt=7)
    farm.harvest_weather(100, harmed=False)

`rows` are what `held_tile_geometry` answers: (tile id, lat, lon, land area km2, arable fraction). Anything else the module
reads is given in `views`; `externality_answers` are what the externality providers answered (each `{"yield_factor_by_tile": ...}`)."""
import random

from sim.agriculture.module import Agriculture
from sim.agriculture.state import AgricultureWorld
from sim.tests import module_harness


def build(rows=(), civ_id="rome_100ad", salt=12345, dice_seed=1, burnt_draws=0, yield_factors=None, views=None, world=None, answers=None,
          externality_answers=None):
    dice = random.Random(dice_seed)
    for _draw in range(burnt_draws):
        dice.random()
    plain = {"civilisation": {"id": civ_id}, "held_tile_geometry": list(rows), "game_random": dice,
             "provider_game": object(),
             "externality": lambda game, year: list(externality_answers if externality_answers is not None else
                                                    [{"yield_factor_by_tile": dict(yield_factors)}] if yield_factors else [])}
    plain.update(views or {})
    return module_harness.build(Agriculture, views=plain, answers=answers,
                                world=world if world is not None else AgricultureWorld(weather_salt=salt), module_id="agriculture")
