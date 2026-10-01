"""Complaint 100: the goal screen shows system leverage, not only the prerequisite chain."""
from .harness import *  # noqa: F401,F403

from sim.engine.proto import command_registry


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


test_sim = sim(capital=1_000_000.0)
leverage = ask(test_sim, cmd="leverage")
check("leverage answers", leverage.get("ok"), leverage)
points = {point["lever"]: point for point in leverage.get("leverage_points", [])}
check("the levers are literacy, labour, finance, institutions, knowledge and materials",
      {"literacy", "labour", "finance", "institutions", "knowledge", "materials"} <= set(points), list(points))
check("every lever shows a figure from the engine and what it unlocks",
      all(point.get("figures") and point.get("why_it_matters") for point in points.values()), points)
check("labour reads the engine's director pool",
      abs(points["labour"]["figures"]["directed_hours_this_year"] - test_sim.director_pool()) < 1, points["labour"])
check("finance reads the engine's recurring net",
      abs(points["finance"]["figures"]["recurring_net_per_year"] - test_sim.recurring_net()) < 1, points["finance"])
check("the reply says a broad approach can be cheaper without prescribing a route",
      "broad" in leverage.get("note", "") and "route" in leverage.get("note", ""), leverage.get("note"))
check("leverage is in the command registry", "leverage" in command_registry.COMMANDS)

path = ask(test_sim, cmd="path", id=test_sim.goal)
check("path carries the leverage points beside the chain",
      path.get("ok") and [point["lever"] for point in path.get("leverage_points", [])] == list(points), path.keys())
check("path says how long following the chain alone would take",
      isinstance(path.get("years_following_the_chain_alone"), (int, float)), path.keys())

fogged = sim(capital=1_000_000.0)
fogged.fog = True
fog_leverage = ask(fogged, cmd="leverage")
check("under fog leverage still answers from the household's own figures",
      fog_leverage.get("ok") and "years_following_the_chain_alone" not in fog_leverage, fog_leverage)
hidden_ids = [node_id for node_id in NODES if not fogged.is_visible(node_id) and len(node_id) > 8]
check("under fog nothing names a node the player has not heard of",
      not any(node_id in str(fog_leverage) for node_id in hidden_ids), "leaked")
