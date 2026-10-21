"""SCENARIO (Complaint 640): Complaint 478: a technique the society gains after the opening reaches the agent economy. The recipes its
producers can run follow the techniques in use; a good that had no market gets one; a saved game resumes
with them; and nothing is rebuilt in a year when nothing changed."""
from .harness import *  # noqa: F401,F403
import os
import tempfile

from sim.engine.saveload import save_state, load_state
from sim.economy import api as economy_api

HEAT = "cap_heat_3000"
GATE = "cn_portland_cement"
NEW_GOOD = "cement_portland_kg"


def recipes_making(game, good):
    return sorted(recipe_id for recipe_id, recipe in game.economy.agent.economy().setup.recipes.items()
                  if good in recipe.outputs)


def put_in_use(game, node_id):
    game.state.projects.done.add(node_id)
    game._done_changed()
    game.state.projects.operating.add(node_id)


game = sim(civ="rome_100ad", capital=1e9)
economy = game.economy.agent.economy()
check("a good nothing offered at the opening has no recipe and no market in the agent economy",
      not recipes_making(game, NEW_GOOD) and NEW_GOOD not in economy.area_map.goods())
opened_recipes = len(economy.setup.recipes)
game._step_market()
check("a year with no new technique changes the economy's recipes not at all",
      len(economy.setup.recipes) == opened_recipes and not game.state.economy.agent_economy.get("late_goods"))

put_in_use(game, HEAT)
put_in_use(game, GATE)
game._step_market()
check("a technique gained after the opening and run gives the economy its recipe",
      bool(recipes_making(game, NEW_GOOD)), recipes_making(game, NEW_GOOD))
check("...and the good it makes gets a market", NEW_GOOD in game.economy.agent.economy().area_map.goods())
check("...and the saved opening lists the recipe, so a resumed game rebuilds it",
      set(recipes_making(game, NEW_GOOD)) <= set(game.state.economy.agent_economy["opening"]["recipes"]))
makers = [producer for producer in economy_api.producers_of(game.economy.agent.economy()).values()
          if NEW_GOOD in game.economy.agent.economy().setup.recipes[producer.recipe_id].outputs]
check("...and producers enter to make it", bool(makers), len(makers))

save_path = os.path.join(tempfile.mkdtemp(), "late_save.json")
save_state(game, save_path)
resumed = sim(civ="rome_100ad", capital=1e9)
load_state(resumed, save_path)
check("a saved game resumes with the late recipe and its market",
      recipes_making(resumed, NEW_GOOD) == recipes_making(game, NEW_GOOD)
      and NEW_GOOD in resumed.economy.agent.economy().area_map.goods())
game.economy.flush_record()
resumed.economy.flush_record()
before = len(game.economy.agent.economy().setup.recipes)
game._step_market()
resumed._step_market()
check("...and a held technique already admitted adds nothing the next year",
      len(game.economy.agent.economy().setup.recipes) == before)
check("...and the resumed game's economy matches the unbroken one's",
      sorted(game.economy.agent.economy().setup.recipes) == sorted(resumed.economy.agent.economy().setup.recipes))
