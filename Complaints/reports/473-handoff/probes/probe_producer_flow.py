import json, random, sys
import numpy
from sim.economy import api as economy_api, goods_turn, economy as economy_mod
from sim.economy.api import EconomyYearInputs
from sim.engine.ui_port import Sim, load, load_civ
from sim.markets import port_sites
log = {}          # (agent) -> dict for the current year
targets = {}      # agent -> (good, tile)
state = {"world": None, "record": None}
ow = goods_turn.TurnWorld.__init__
def init(self, *a, **k):
    ow(self, *a, **k); state["world"] = self
goods_turn.TurnWorld.__init__ = init
op = goods_turn.TurnWorld.produce
def produce(self, positions):
    ids = self.arrays.producers.ids; book = self.record.book
    for p in positions.tolist():
        a = ids[p]
        if a in targets:
            g, t = targets[a]; c = self.arrays.producers
            d = log.setdefault(a, {})
            d.update(stock_start=book.stock(a, g, t), runs_plan=float(self.runs[p]), capacity=float(c.capacity_runs[p]),
                     last_runs=float(c.last_runs[p]), expected_sales=float(c.expected_sales[p]), cash_target=float(c.cash_target[p]),
                     cash=float(book.balances_at(self.agents.array()[[p]], self.setup.currency_id)[0]), yield_factor=float(c.yield_factor[p]))
    r = op(self, positions)
    for p in positions.tolist():
        a = ids[p]
        if a in targets:
            g, t = targets[a]; log[a]["stock_after_prod"] = book.stock(a, g, t)
    return r
goods_turn.TurnWorld.produce = produce
ow2 = goods_turn.TurnWorld._write
def write(self, orders, owners, good_rows, units, reservation):
    ids = self.arrays.producers.ids
    for o, gr, u, rs in zip(owners.tolist(), good_rows.tolist(), units.tolist(), reservation.tolist()):
        a = ids[o]
        if a in targets and self.arrays.matrices.goods.ids[gr] == targets[a][0]:
            log.setdefault(a, {}).setdefault("lots", []).append((round(u, 1), round(rs, 1)))
    return ow2(self, orders, owners, good_rows, units, reservation)
goods_turn.TurnWorld._write = write
oc = economy_mod.clear_goods
def clear(setup, record, view, area_map, order_book, plans, ledger, *a, **k):
    r = oc(setup, record, view, area_map, order_book, plans, ledger, *a, **k)
    for ag, (g, t) in targets.items():
        d = log.setdefault(ag, {})
        try: d["sold"] = float(ledger.sold.get((ag, g), 0.0))
        except Exception as e: d["sold"] = repr(e)
        try: d["made"] = float(ledger.output.get((ag, g), 0.0))
        except Exception as e: d["made"] = repr(e)
        d["stock_end_clear"] = record.book.stock(ag, g, t)
    return r
economy_mod.clear_goods = clear

from sim.economy import goods_good_clear
gc = goods_good_clear.clear_good
mk = {}
def clear_good(context, good, good_id, *a, **k):
    r = gc(context, good, good_id, *a, **k)
    if good in ("ox", "mule") and len(r.market):
        rows = []
        for p in range(len(r.market)):
            bids = context.orders.bids_of(r.rows.bids_of_market(p)) if r.rows is not None else []
            rows.append(dict(area=r.areas[p], qty=float(r.quantity[p]), price=float(r.price[p]), demand=float(r.demand[p]), offered=float(r.offered[p]),
                wanted=float(r.wanted[p]), quote=float(r.quote_price[p]), nbids=len(bids),
                bids=[(b.buyer, round(getattr(b,"quantity",0) or 0,1), getattr(b,"maximum_price",None)) for b in bids[:8]] if p == 0 or r.offered[p] > 0 else []))
        mk[good] = rows
    return r
goods_good_clear.clear_good = clear_good
civ, fy, ty, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
_t,_p,nodes,_w,_g = load()
game = Sim(nodes, [], random.Random(1), events=False, manual=True, civ=load_civ(civ))
setup = game.view("agent_opening_setup")()
economy = economy_api.blank_economy(setup); economy_api.begin_spin_up(economy)
inputs = EconomyYearInputs(year=0, population_by_tile={}, yield_factor_by_producer=port_sites.crop_yields(economy), engine_orders={})
with open(out, "w") as h:
    for stage, years in (("first", fy), ("trimmed", ty)):
        if stage == "trimmed": economy_api.trim_workforce_to_expected_hours(economy)
        for year in range(years):
            if not targets:
                for a, pr in economy.record.producers.items():
                    outs = setup.recipes[pr.recipe_id].outputs
                    for g in ("ox", "mule"):
                        if g in outs and pr.tile == "france_05": targets[a] = (g, pr.tile)
                    if "wood_kg" in outs and pr.tile == "germany_01" and len([1 for v in targets.values() if v[0]=="wood_kg"]) < 3: targets[a] = ("wood_kg", pr.tile)
                print(targets, flush=True)
            log.clear(); mk.clear()
            o = economy.step(inputs)
            rec = economy.record
            for a, (g, t) in targets.items():
                d = log.setdefault(a, {}); d["stock_end"] = rec.book.stock(a, g, t); d["price"] = o.prices.get(g)
                d["recipe"] = rec.producers[a].recipe_id; d["good"] = g
                d["cash_end"] = float(rec.book.balances_at(numpy.array([rec.book.agent_ids.numbers[a]]), setup.currency_id)[0])
            h.write(json.dumps(dict(stage=stage, year=year, rate=economy_api.interest_rate(economy), d=log, mk=mk), default=float) + "\n"); h.flush()
            print(stage, year, flush=True)
