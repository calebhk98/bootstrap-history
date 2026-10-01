"""Complaints/147: a project pays for the materials it is MISSING, at today's
market price, and draws owned stock first.

A research node declares only quantities. The economy prices what is missing
at the same quote `quote material` shows, and buying a large amount raises the
price through the market's own scarcity curve.
"""
import os

from .harness import *  # noqa: F401,F403

_LEAD = "lead_metallurgy"
_SMALL = "tex_horizontal_loom"

# --- stock is drawn first: holding a material lowers the bill -----------------
_held_sim = sim(capital=5e7)
_cost_empty = _held_sim.project_cost(_LEAD)
_needed = {row["material"]: row["needed_tonnes"]
           for row in _held_sim.project_material_bill(_LEAD)["rows"]}
_spent_before = _held_sim.capital
_bought = {}
for _material, _tonnes in sorted(_needed.items()):
    _bought[_material] = _held_sim.buy_material_stock(_material, _tonnes)
_paid = _spent_before - _held_sim.capital
_cost_held = _held_sim.project_cost(_LEAD)
check("stock: the materials were bought in full",
      all(abs(_bought[key] - _needed[key]) < 1e-6 for key in _needed), (_bought, _needed))
check("stock: holding the materials takes their market value off the project cost",
      _cost_held <= _cost_empty - 0.9 * _paid, (_cost_empty, _cost_held, _paid))

# --- the bill: needed, held, missing, cost of the missing part ----------------
_bill = _held_sim.project_material_bill(_LEAD)
_rows = {row["material"]: row for row in _bill["rows"]}
check("bill: one row per material the node needs",
      set(_rows) == set(_needed) and len(_rows) >= 2, sorted(_rows))
check("bill: bought tonnes show as held and nothing is missing",
      all(row["missing_tonnes"] < 1e-6 and row["held_tonnes"] >= row["needed_tonnes"] - 1e-6
          for row in _rows.values()), _rows)
check("bill: with everything held the materials part of the cost is zero",
      _bill["cost_of_missing"] < 1e-6, _bill["cost_of_missing"])

_fresh = sim(capital=5e7)
_fresh_bill = _fresh.project_material_bill(_LEAD)
check("bill: with nothing held every needed tonne is missing",
      all(abs(row["missing_tonnes"] - row["needed_tonnes"]) < 1e-6
          for row in _fresh_bill["rows"]), _fresh_bill["rows"])
check("bill: the total of the rows is the cost of the missing part",
      abs(sum(row["cost_of_missing"] for row in _fresh_bill["rows"])
          - _fresh_bill["cost_of_missing"]) < 1e-6 * max(1.0, _fresh_bill["cost_of_missing"]),
      _fresh_bill)

# --- missing part priced at the current market quote --------------------------
_small = sim()
_small_bill = _small.project_material_bill(_SMALL)
for _row in _small_bill["rows"]:
    _quote = _small.material_trade_quote(_row["material"])
    _units_per_tonne = 1e6 if _row["material"].endswith("_g") else 1e3
    _expected = _row["needed_tonnes"] * _quote["buy_per_tonne"] * (
        1e3 / _units_per_tonne)
    check("market: %s is priced at the `quote material` price" % _row["material"],
          abs(_row["cost_of_missing"] - _expected) <= 0.02 * max(_expected, 1e-9),
          (_row["cost_of_missing"], _expected))

# --- buying is demand: a large purchase raises the price it is bought at ------
_price_sim = sim(capital=5e7)
_one_tonne = _price_sim.material_trade_quote("coal")["buy_per_tonne"]
_capital_before = _price_sim.capital
_got = _price_sim.buy_material_stock("coal", 2000.0)
_average_paid = (_capital_before - _price_sim.capital) / max(_got, 1e-9)
check("price: a 2000 t purchase was delivered", _got > 1900.0, _got)
check("price: the large purchase paid more per tonne than the one-tonne quote",
      _average_paid > 1.05 * _one_tonne, (_average_paid, _one_tonne))
_small_sim = sim(capital=5e7)
_capital_before = _small_sim.capital
_small_sim.buy_material_stock("coal", 200.0)
check("price: a smaller purchase pays less per tonne than a larger one",
      (_capital_before - _small_sim.capital) / 200.0 < _average_paid,
      ((_capital_before - _small_sim.capital) / 200.0, _average_paid))

# --- `why` shows the rows and the same total the engine charges ---------------
_why = proto([{"cmd": "why", "id": _LEAD}])[0][0]
_why_rows = _why.get("material_rows") or []
check("why: the reply carries a row per material with needed, held, missing and cost",
      bool(_why_rows) and all(
          {"material", "needed_tonnes", "held_tonnes", "missing_tonnes", "cost_of_missing"}
          <= set(row) for row in _why_rows), _why.get("material_rows"))
_reference = sim()
check("why: the headline total is what the engine charges (held-aware)",
      abs(_why["cost"]["total"] - round(_reference.project_cost(_LEAD), 1)) < 1.0,
      (_why["cost"]["total"], _reference.project_cost(_LEAD)))
check("why: the headline materials figure is the cost of the missing part",
      abs(_why["cost"]["materials"]
          - round(_reference.project_material_bill(_LEAD)["cost_of_missing"], 1)) < 1.0,
      _why["cost"])

# --- starting pays for the missing materials and delivers them ----------------
_start_sim = sim(capital=5e7)
run_it(_start_sim, *_start_sim.nodes[_LEAD]["pre"])
_start_sim.artisans = _start_sim.scholars = 50.0
_fuel_key = _start_sim._material_tag(sorted(_needed)[0])[0]
_stock_before = _start_sim.material_stock_t(_fuel_key)
_capital_before = _start_sim.capital
_started, _why_not = _start_sim.start_project(_LEAD)
check("start: the project starts", _started, _why_not)
check("start: the missing materials were paid for at the start",
      _capital_before - _start_sim.capital > 0.0, _start_sim.capital)
check("start: the money delivered stock",
      _start_sim.material_stock_t(_fuel_key) > _stock_before,
      (_stock_before, _start_sim.material_stock_t(_fuel_key)))

# --- research data authors never touch prices ---------------------------------
_module = os.path.join(ROOT, "sim", "engine", "project_materials.py")
check("no reader of prices.json in the project materials module",
      os.path.exists(_module) and "prices.json" not in open(_module).read()
      and "PRICES" not in open(_module).read(), _module)

# --- the bill fixed at the start survives a save and a load, and is not re-priced
from sim.engine.proto.saveload import save_state, load_state
_frozen = _start_sim.project_cost(_LEAD)
_path = os.path.join(tempfile.mkdtemp(), "bill.json")
save_state(_start_sim, _path)
_reloaded = sim(capital=1.0)
load_state(_reloaded, _path)
check("start: the instalment bill is fixed at the start and survives save/load",
      abs(_reloaded.project_cost(_LEAD) - _frozen) < 1e-6 and _frozen > 0,
      (_reloaded.project_cost(_LEAD), _frozen))
_start_sim.buy_material_stock("coal", 500.0)
check("start: buying stock afterwards does not change a running project's bill",
      abs(_start_sim.project_cost(_LEAD) - _frozen) < 1e-6, (_start_sim.project_cost(_LEAD), _frozen))

# --- a bounty is a multiple of what this society would pay to build it -------
_bounty_sim = sim(capital=5e7)
check("bounty: priced from the same market-priced cost as the build",
      abs(_bounty_sim.bounty_price(_LEAD)
          - _bounty_sim.BOUNTY_PRICE_MULTIPLIER * _bounty_sim.project_cost(_LEAD)
          / _bounty_sim.opposition_factor(_LEAD)) < 1e-6,
      _bounty_sim.bounty_price(_LEAD))

# --- `quote material` charges what `buy material` charges for the same order ---
from sim.engine.proto.dispatch_money import _cmd_quote
_quote_sim = sim(capital=5e7)
_quoted = _cmd_quote(_quote_sim, NODES, {"what": "material", "material": "coal", "n": 2000}, None)
_before = _quote_sim.capital
_quote_sim.buy_material_stock("coal", 2000.0)
check("quote: the quoted price for an order is what buying it costs",
      abs(_quoted["to_buy_it"] - (_before - _quote_sim.capital)) < 1.0,
      (_quoted["to_buy_it"], _before - _quote_sim.capital))
