"""Living stock is bought from a partner and turns each year (Complaints/366, 365): the whole-game scenarios.

The yearly rule and the data rows are test_living_stock_trade. Here the buy command charges its quote, refusals say why,
a year of the game turns held stock by the stated rates, and the screens show it."""

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
      not refused.get("ok") and refused.get("cause") == "partner_export_held_back", refused)
check("a refusal delivers nothing", buyer.stock_held(EGGS) == 0.0, buyer.stock_held(EGGS))
refused_quote = S._agent_dispatch(buyer, NODES, {"cmd": "quote", "what": "living_stock", "material": EGGS, "n": 0.1})
check("the quote refuses with the same reason",
      not refused_quote.get("ok") and refused_quote.get("cause") == "partner_export_held_back", refused_quote)
more = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": RAMIE, "n": 1e9})
check("a partner cannot sell more than it holds", not more.get("ok") and more.get("cause") == "partner_holds_less", more)
poor = sim(civ=HOME, capital=1.0)
poor.goods_market.acting.can_pay = lambda money: False
broke = S._agent_dispatch(poor, NODES, {"cmd": "buy", "what": "living_stock", "material": RAMIE, "n": 1000})
check("a buyer who cannot pay is refused and charged nothing",
      not broke.get("ok") and poor.stock_held(RAMIE) == 0.0, broke)
unknown = S._agent_dispatch(buyer, NODES, {"cmd": "buy", "what": "living_stock", "material": "hammer", "n": 1})
check("a material no partner makes is refused", not unknown.get("ok"), unknown)


with open(os.path.join(ROOT, "data", "world", "living_stock.json"), encoding="utf-8") as handle:
    rates = json.load(handle)["materials"]

# --- the year turns the held stock.
herd = unopened_sim(civ=HOME, capital=1e6)
herd.grant_stock(HERD, 10000.0)
herd.step_living_stock()
expected = stock_dynamics.next_units(
    10000.0, rates[HERD]["natural_increase"], rates[HERD]["annual_loss"], rates[HERD]["breeding_minimum_units"])
check("a herd above its minimum grows over a year", herd.stock_held(HERD) > 10000.0, herd.stock_held(HERD))
check("the growth is the stated rule", abs(herd.stock_held(HERD) - expected) < 1e-6, (herd.stock_held(HERD), expected))
small = unopened_sim(civ=HOME, capital=1e6)
small.grant_stock(HERD, rates[HERD]["breeding_minimum_units"] / 2.0)
held_then = small.stock_held(HERD)
small.step_living_stock()
check("a herd below the breeding minimum does not grow", small.stock_held(HERD) < held_then,
      (held_then, small.stock_held(HERD)))
eggs = unopened_sim(civ=HOME, capital=1e6)
eggs.grant_stock(EGGS, 1.0)
eggs.step_living_stock()
check("stored eggs are lost to spoilage and not multiplied", eggs.stock_held(EGGS) < 1.0, eggs.stock_held(EGGS))
empty = unopened_sim(civ=HOME, capital=1e6)
empty.step_living_stock()
check("a society holding no stock gains none", empty.stock_held(HERD) == 0.0, None)

# --- held stock on the screens (Complaints/86): `state` and `available` show it, small.
from sim.ui.proto.render_screen_state import render_state  # noqa: E402
from sim.ui.proto.tree_filters import render_state_rows  # noqa: E402

shown = unopened_sim(civ=HOME, capital=1e6)
bare = S._agent_dispatch(shown, NODES, {"cmd": "state"})
check("state lists no eggs while none are held", EGGS not in (bare.get("living_stock") or {}), bare.get("living_stock"))
blocked = S._agent_dispatch(shown, NODES, {"cmd": "available", "find": "tx2_silk_fibre", "state": "blocked"})
row = next((entry for entry in blocked.get("rows", []) if entry["id"] == "tx2_silk_fibre"), {})
check("a blocked row names the stock it needs, held beside needed",
      row.get("living_stock") == [{"material": EGGS, "needed": 0.02, "held": 0.0}], row)
check("the blocked list prints the held line", "HELD: %s 0 of 0.02 needed" % EGGS in render_state_rows(blocked),
      render_state_rows(blocked))
shown.grant_stock(EGGS, 0.5)
held_state = S._agent_dispatch(shown, NODES, {"cmd": "state"})
check("state lists the living stock held", held_state.get("living_stock") == dict(bare.get("living_stock") or {}, **{EGGS: 0.5}),
      held_state.get("living_stock"))
check("the state screen prints it",
      "%s 0.5" % EGGS in render_state(held_state), None)
startable = S._agent_dispatch(shown, NODES, {"cmd": "available", "find": "tx2_silk_fibre", "state": "startable"})
row = next((entry for entry in startable.get("available", []) if entry["id"] == "tx2_silk_fibre"), {})
check("a startable row shows the stock held beside the stock needed",
      row.get("living_stock") == [{"material": EGGS, "needed": 0.02, "held": 0.5}], startable)
