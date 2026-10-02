"""Living stock is bought from a partner, breeds and dies each year (Complaints/366, 365).

A player buys held stock through `buy living_stock`, priced at the partner's price plus the merchants'
terms and freight and paid through the one goods market; the quote is the charge. A partner that will
not sell refuses with the reason. Held stock grows by its natural increase once the herd is large
enough to breed and falls by its losses; each rate is data with a stated basis.
"""
import json

from .harness import *  # noqa: F401,F403

from sim.engine.data import ROOT
from sim.world import stock_dynamics

HOME, PARTNER = "rome_100ad", "han_china_100ad"
EGGS, RAMIE, HERD = "silkworm_eggs_kg", "ramie_stock_kg", "draught_animal_kg"

# --- the buy command: priced at the partner's price, paid, delivered.
buyer = sim(civ=HOME, capital=1e7)
reply = S._agent_dispatch(buyer, NODES, {"cmd": "quote", "what": "living_stock", "material": RAMIE, "n": 100})
check("a partner that sells ramie stock is quoted", reply.get("ok") and reply.get("to_buy_it", 0) > 0, reply)
check("the quote names the partner and its price per tonne",
      reply.get("partner") == PARTNER and reply.get("per_tonne", 0) > 0, reply)
cash_before = buyer.capital
bought = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": RAMIE, "n": 100})
check("the purchase succeeds", bought.get("ok"), bought)
check("the stock is held after buying it", abs(buyer.stock_held(RAMIE) - 100.0) < 1e-6, buyer.stock_held(RAMIE))
check("the charge is the quote", abs((cash_before - buyer.capital) - reply["to_buy_it"]) <= 0.051,
      (cash_before - buyer.capital, reply["to_buy_it"]))
check("the quote is built from the partner price, merchants' terms and freight",
      abs(reply["to_buy_it"] - buyer.partner_quote_per_tonne(RAMIE, PARTNER) * 100.0 * 0.001) <= 0.06,
      (reply["to_buy_it"], buyer.partner_quote_per_tonne(RAMIE, PARTNER)))

# --- refusals say why.
refused = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": EGGS, "n": 0.1})
check("a partner that will not sell eggs is refused, with the reason",
      not refused.get("ok") and "will not sell" in refused.get("error", ""), refused)
check("a refusal delivers nothing", buyer.stock_held(EGGS) == 0.0, buyer.stock_held(EGGS))
refused_quote = S._agent_dispatch(buyer, NODES, {"cmd": "quote", "what": "living_stock", "material": EGGS, "n": 0.1})
check("the quote refuses with the same reason",
      not refused_quote.get("ok") and "will not sell" in refused_quote.get("error", ""), refused_quote)
more = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": RAMIE, "n": 1e9})
check("a partner cannot sell more than it holds", not more.get("ok") and "holds" in more.get("error", ""), more)
poor = sim(civ=HOME, capital=1.0)
poor.goods_market.founder.can_pay = lambda money: False
broke = S._agent_dispatch(poor, NODES, {"cmd": "buy", "what": "living_stock", "material": RAMIE, "n": 1000})
check("a buyer who cannot pay is refused and charged nothing",
      not broke.get("ok") and poor.stock_held(RAMIE) == 0.0, broke)
unknown = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": "hammer", "n": 1})
check("a material no partner makes is refused", not unknown.get("ok"), unknown)

# --- the yearly rule: increase only from a herd that can breed, loss always.
check("a herd at or above the breeding minimum grows by its natural increase less its loss",
      abs(stock_dynamics.next_units(100.0, 0.2, 0.05, 10.0) - 115.0) < 1e-9, None)
check("a herd below the breeding minimum cannot grow, and still falls by its loss",
      abs(stock_dynamics.next_units(5.0, 0.2, 0.05, 10.0) - 4.75) < 1e-9, None)
check("stock never goes negative", stock_dynamics.next_units(1.0, 0.0, 1.5, 0.0) == 0.0, None)

with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
    rates = json.load(handle)["materials"]
for material, row in sorted(rates.items()):
    check("%s: increase and loss are fractions of the herd and the minimum is not negative" % material,
          0.0 <= row["natural_increase"] <= 1.0 and 0.0 <= row["annual_loss"] <= 1.0
          and row["breeding_minimum_units"] >= 0.0, row)
    check("%s: each rate states its basis" % material, len(row.get("basis", "")) > 40, row.get("basis"))

# --- the year turns the held stock.
herd = sim(civ=HOME, capital=1e6)
herd.grant_stock(HERD, 10000.0)
herd.step_living_stock()
expected = stock_dynamics.next_units(
    10000.0, rates[HERD]["natural_increase"], rates[HERD]["annual_loss"], rates[HERD]["breeding_minimum_units"])
check("a herd above its minimum grows over a year", herd.stock_held(HERD) > 10000.0, herd.stock_held(HERD))
check("the growth is the stated rule", abs(herd.stock_held(HERD) - expected) < 1e-6, (herd.stock_held(HERD), expected))
small = sim(civ=HOME, capital=1e6)
small.grant_stock(HERD, rates[HERD]["breeding_minimum_units"] / 2.0)
held_then = small.stock_held(HERD)
small.step_living_stock()
check("a herd below the breeding minimum does not grow", small.stock_held(HERD) < held_then,
      (held_then, small.stock_held(HERD)))
eggs = sim(civ=HOME, capital=1e6)
eggs.grant_stock(EGGS, 1.0)
eggs.step_living_stock()
check("stored eggs are lost to spoilage and not multiplied", eggs.stock_held(EGGS) < 1.0, eggs.stock_held(EGGS))
empty = sim(civ=HOME, capital=1e6)
empty.step_living_stock()
check("a society holding no stock gains none", empty.stock_held(HERD) == 0.0, None)
stepped = sim(civ=HOME, capital=1e6)
stepped.grant_stock(HERD, 10000.0)
stepped.step()
check("a year of the game turns the held stock", abs(stepped.stock_held(HERD) - 10000.0) > 1.0,
      stepped.stock_held(HERD))

# --- the stock nodes converted from research: each holds a stock material, a venture brings it.
for consumer, material in (("tx2_cashmere", "cashmere_goat_kg"), ("tx2_mohair", "angora_goat_kg"),
                           ("tx2_jute_fibre", "jute_seed_kg"), ("ag2_hopping", "hop_rhizome_kg"),
                           ("ag2_pyrethrum", "pyrethrum_stock_kg")):
    node = NODES[consumer]
    check("%s holds %s and names no stand-in stock node" % (consumer, material),
          material in (node.get("holds") or {}) and not any(pre.endswith("_stock") for pre in node["pre"]),
          (node.get("holds"), node["pre"]))
    brought_by = [node_id for node_id, other in NODES.items() if material in (other.get("grants") or {})]
    check("%s is brought back by a venture that grants it" % material, bool(brought_by), None)
    check("%s breeds under a stated rule" % material, material in rates, None)

# --- held stock on the screens (Complaints/86): `state` and `available` show it, small.
from sim.engine.proto.render_screens_big import render_state  # noqa: E402
from sim.engine.proto.tree_filters import render_state_rows  # noqa: E402

shown = sim(civ=HOME, capital=1e6)
bare = S._agent_dispatch(shown, NODES, {"cmd": "state"})
check("state lists no living stock while none is held", "living_stock" not in bare, bare.get("living_stock"))
blocked = S._agent_dispatch(shown, NODES, {"cmd": "available", "find": "tx2_silk_fibre", "state": "blocked"})
row = next((entry for entry in blocked.get("rows", []) if entry["id"] == "tx2_silk_fibre"), {})
check("a blocked row names the stock it needs, held beside needed",
      row.get("living_stock") == [{"material": EGGS, "needed": 0.02, "held": 0.0}], row)
check("the blocked list prints the held line", "HELD: %s 0 of 0.02 needed" % EGGS in render_state_rows(blocked),
      render_state_rows(blocked))
shown.grant_stock(EGGS, 0.5)
held_state = S._agent_dispatch(shown, NODES, {"cmd": "state"})
check("state lists the living stock held", held_state.get("living_stock") == {EGGS: 0.5},
      held_state.get("living_stock"))
check("the state screen prints it on one line",
      "LIVING STOCK HELD: %s 0.5" % EGGS in render_state(held_state), None)
startable = S._agent_dispatch(shown, NODES, {"cmd": "available", "find": "tx2_silk_fibre", "state": "startable"})
row = next((entry for entry in startable.get("available", []) if entry["id"] == "tx2_silk_fibre"), {})
check("a startable row shows the stock held beside the stock needed",
      row.get("living_stock") == [{"material": EGGS, "needed": 0.02, "held": 0.5}], startable)
