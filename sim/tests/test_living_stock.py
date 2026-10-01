"""Living stock is held, not researched (Complaints/365, 133).

Silkworm eggs are a material held at a place. A node that needs them (`holds`) opens by itself
once they are held, however they were got: an opening holding, a purchase from a partner that
offers them, or a grant. A country refusing to sell is that country's own `will_not_sell` data.
"""
from .harness import *  # noqa: F401,F403

from sim.engine import foreign_economies as _foreign_module
from sim.engine.data import load_civ

EGGS = "silkworm_eggs_kg"
HOME, PARTNER = "rome_100ad", "han_china_100ad"

_shipped_records = _foreign_module.foreign_economy_records
_foreign_module.foreign_economy_records = lambda: tuple(
    dict(record, enabled=True) for record in _shipped_records())

# --- the stand-ins are gone and no route node stands in for the stock.
check("the native-stock stand-in node is gone", "tx2_silkworm_native_stock" not in NODES, None)
check("the acquire-the-stock research node is gone", "tx2_silkworm_stock" not in NODES, None)
for _node_id in ("tx2_silk_fibre", "tx2_sericulture"):
    _node = NODES[_node_id]
    _options = {option for group in _node.get("req_any") or [] for option in group["options"]}
    check("%s needs the eggs held and no route node" % _node_id,
          EGGS in (_node.get("holds") or {}) and "sea_monsoon_route" not in _node["pre"]
          and "sea_monsoon_route" not in _options, _node.get("holds"))
check("the partner's starting techs name no stock node",
      not {"tx2_silkworm_stock", "tx2_silkworm_native_stock"} & set(load_civ(PARTNER)["starting_techs"]), None)

# --- the home holds no eggs and cannot take sericulture; the route node is no way round.
home = sim(civ=HOME, capital=1e9)
home.state.projects.done.discard("sea_monsoon_route")
home._done_changed()
check("a society without eggs holds none", home.stock_held(EGGS) == 0.0, home.stock_held(EGGS))
_ok, _why = home.start_reason("tx2_silk_fibre")
check("without the eggs the first silk node is refused, naming the eggs",
      not _ok and EGGS in (_why or ""), _why)
check("...and the refusal is a supply blocker naming no route",
      any(entry["kind"] == "supply" for entry in home.start_blockers("tx2_silk_fibre"))
      and "sea_monsoon_route" not in (_why or ""), home.start_blockers("tx2_silk_fibre"))

# --- a grant opens the node and nothing else changes.
check("holding eggs is not itself a known technology", EGGS not in home.state.projects.done, None)
home.grant_stock(EGGS, 1.0)
check("a grant is held", home.stock_held(EGGS) >= 1.0, home.stock_held(EGGS))
check("holding the eggs opens the first silk node with no other change",
      home.start_reason("tx2_silk_fibre")[0], home.start_reason("tx2_silk_fibre"))
home.state.projects.done.add("tx2_silk_fibre")
home._done_changed()
check("...and then sericulture, with no route node",
      "sea_monsoon_route" not in home.state.projects.done and home.start_reason("tx2_sericulture")[0],
      home.start_reason("tx2_sericulture"))

# --- the partner starts holding eggs; its sericulture rests on them.
han = sim(civ=PARTNER, capital=1e9)
check("the partner opens holding eggs", han.stock_held(EGGS) > 0.0, han.stock_held(EGGS))
check("so no node of its own is missing a stock",
      not han.stock_missing("tx2_sericulture") and not han.stock_missing("tx2_silk_fibre"), None)
check("the partner lists eggs among what it will not sell",
      EGGS in load_civ(PARTNER).get("will_not_sell", ()), load_civ(PARTNER).get("will_not_sell"))

# --- the partner's refusal is its own policy: the foreign trade refuses, the data decides.
buyer = sim(civ=HOME, capital=1e9)
check("a partner that refuses to sell eggs sells none",
      buyer.buy_stock_from_partner(EGGS, 0.1, PARTNER) == 0.0 and buyer.stock_held(EGGS) == 0.0,
      buyer.stock_held(EGGS))
check("...and says so", "will not sell" in (buyer.partner_refusal(PARTNER, EGGS) or ""),
      buyer.partner_refusal(PARTNER, EGGS))

# --- a partner that offers them: the purchase is paid for and opens the node.
_shipped_refused = _foreign_module.exports_refused
_foreign_module.exports_refused = lambda civilization_id: frozenset()
buyer = sim(civ=HOME, capital=1e9)
buyer.state.projects.done.discard("sea_monsoon_route")
buyer._done_changed()
_cash_before = buyer.state.household.capital
check("before buying, the node is refused", not buyer.start_reason("tx2_silk_fibre")[0], None)
_got = buyer.buy_stock_from_partner(EGGS, 0.1, PARTNER)
check("a partner that offers eggs sells them", abs(_got - 0.1) < 1e-9 and buyer.stock_held(EGGS) >= 0.1, _got)
check("the purchase costs money", buyer.state.household.capital < _cash_before, None)
check("the purchase opens the node with no other change",
      buyer.start_reason("tx2_silk_fibre")[0] and "sea_monsoon_route" not in buyer.state.projects.done,
      buyer.start_reason("tx2_silk_fibre"))
check("a good the partner cannot make is not for sale",
      buyer.buy_stock_from_partner("hammer_forged_kg_nonexistent", 1.0, PARTNER) == 0.0, None)
_foreign_module.exports_refused = _shipped_refused

# --- stock survives a save and load within a build.
from sim.engine.proto.saveload import load_state, save_state
with tempfile.TemporaryDirectory() as _folder:
    _path = os.path.join(_folder, "save.json")
    save_state(buyer, _path)
    _revived = sim(civ=HOME, capital=1e9)
    load_state(_revived, _path)
check("held stock round-trips through save and load",
      abs(_revived.stock_held(EGGS) - buyer.stock_held(EGGS)) < 1e-12 and _revived.stock_held(EGGS) > 0.0,
      (_revived.stock_held(EGGS), buyer.stock_held(EGGS)))

# --- a draught-animal gate is lifted by holding the animals, however they came.
_mexica = sim(civ="mexica_1500", capital=1e9)
_gate, _because = _mexica.needs_first("horse_collar")
check("a society holding no draught animals is gated", _gate == "exp_import_draught_animals", _gate)
_mexica.grant_stock("draught_animal_kg", 2000.0)
check("holding draught animals lifts the gate with no research",
      _mexica.needs_first("horse_collar")[0] is None, _mexica.needs_first("horse_collar"))
check("the founding-herd voyage grants the herd it brings",
      (NODES["exp_import_draught_animals"].get("grants") or {}).get("draught_animal_kg", 0) > 0,
      NODES["exp_import_draught_animals"].get("grants"))

# --- one crop seed stock: ramie propagation stock, held by the partner, bought by others.
check("the ramie stock research node is gone and the fibre needs the stock held",
      "tx2_ramie_plant_stock" not in NODES
      and "ramie_stock_kg" in (NODES["tx2_ramie_fibre"].get("holds") or {}), None)
check("the partner opens holding ramie stock",
      sim(civ=PARTNER).stock_held("ramie_stock_kg") > 0.0, None)
