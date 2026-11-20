"""Every year of every member of a spin-up ensemble, as `spin-up-trace --stages --ensemble` replays them
(sim.markets.spin_up_stages.replay_opening; member k's households' cash is scaled by spin_up_ensemble.cash_factor(k)).
One JSON line per member and year. Members run one after another in this process.
Usage: [ABLATE=name,name] python3 ensemble_years.py <civ> <members> <out.jsonl>"""
import json, random, sys, time
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import spin_up_stages
from sim.markets.spin_up_ensemble import cash_factor

civ, members, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
_tree, _prices, nodes, _wages, _goods = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
import os
if os.environ.get("ABLATE"):       # experiment switches (ablations.py beside this file)
    import ablations
    ablations.apply(os.environ["ABLATE"])
with open(out, "w") as handle:
    for member in range(members):
        started = time.time()
        watched, rows = spin_up_stages.replay_opening(setup, cash_factor(member))
        for row in rows:
            kept = {name: row.get(name) for name in ("stage", "year", "price_level", "rate", "real_output", "hired_hours", "inventory_value",
                                                     "unmet_need", "food_need", "wage", "money_supply")}
            kept["prices"] = row.get("prices")
            kept["price_weights"] = row.get("price_weights")
            kept["member"] = member
            handle.write(json.dumps(kept, default=float) + "\n")
        handle.flush()
        print("member", member, round(time.time() - started), "s", flush=True)
