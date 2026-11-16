import json, random, sys
import numpy
from sim.economy import api as economy_api
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
from sim.economy import credit_clearing as cc
from sim.loans import clearing_kernel as ck
civ, first_years, trimmed_years, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
calls = []
orig = cc.run_kernel
def wrapped(requests, offers, last_rate, rate_ceiling, expected_inflation):
    status, scalars, loans = orig(requests, offers, last_rate, rate_ceiling, expected_inflation)
    n = int(requests.row_count[0]); m = int(offers.row_count[0])
    lowest = float(ck.lowest_rate(offers))
    ck.price_requests(requests, offers, lowest, cc.constants())
    able = ck.able_to_borrow(requests, max(0.0, lowest))
    _f, target = ck.target_rate(requests, offers, able, cc.constants())
    calls.append(dict(last=last_rate, out=float(scalars[0]) if scalars[1] else None, status=int(status), target=float(target), lowest_ask=lowest,
        ceiling=rate_ceiling, infl=expected_inflation, n_req=n, n_able=int(able.sum()), req_total=float(requests.funded_amount[:n].sum()),
        funds=float(offers.amount[:m].sum()), n_off=m, max_ceiling=float(requests.ceiling[:n].max()) if n else None,
        offer_asks=sorted(set(round(float(a),5) for a in offers.minimum_rate[:m]))[:8]))
    return status, scalars, loans
cc.run_kernel = wrapped
_t,_p,nodes,_w,_g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup); economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
with open(out, "w") as h:
    for stage, years in (("first", first_years), ("trimmed", trimmed_years)):
        if stage == "trimmed": economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            calls.clear()
            outcome = economy.step(inputs)
            h.write(json.dumps(dict(stage=stage, year=year, rate=economy_api.interest_rate(economy), calls=list(calls)), default=float)+"\n"); h.flush()
