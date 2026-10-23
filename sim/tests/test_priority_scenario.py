"""Scenario (Complaint 89): in a running game the rank `priority` sets is the rank the next step hands hours out by.
The command's rules are in test_priority."""
from .harness import *  # noqa: F401,F403

_ids = ["academy_network", "corpus_written", "school_founded"]

game = unopened_sim(capital=1e7)
game.order = list(_ids)
game.active.clear()
game.hour_allocations.clear()
for node_id in _ids:
    game.active[node_id] = dict(ph_left=float(NODES[node_id]["ph"]), yrs=0.0, spent=0.0, cost_left=0.0, lab_left={})
reply = S._agent_dispatch(game, NODES, dict(cmd="priority", id="school_founded", position="first"))
check("priority puts the project first", reply.get("ok") and reply["order"][0] == "school_founded", reply)
game.step()
ranks_after_step = [game.active[node_id]["pool_rank_this_year"] for node_id in _ids]
check("step() hands out hours in that order", ranks_after_step == [2, 3, 1], ranks_after_step)
