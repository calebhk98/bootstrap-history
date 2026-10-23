"""Living stock is held, not researched (Complaints/365, 133): the whole-game scenarios.

The data the nodes and partners carry is test_living_stock. Here a game shows that holding the eggs opens the node however
they were got, that a refusing partner sells none, and that stock survives a save."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of

from sim.engine import foreign_economies as _foreign_module
from sim.engine.agents_port_cast import seed_opening_cast
from sim.engine.data import load_civ

EGGS = "silkworm_eggs_kg"
HOME, PARTNER = "rome_100ad", "han_china_100ad"

_shipped_records = _foreign_module.foreign_economy_records
_foreign_module.foreign_economy_records = lambda: tuple(
    dict(record, enabled=True) for record in _shipped_records())

# --- the home holds no eggs and cannot take sericulture; the route node is no way round.
home = unopened_sim(civ=HOME, capital=1e9)
home.state.projects.done.discard("sea_monsoon_route")
home._done_changed()
check("a society without eggs holds none", home.stock_held(EGGS) == 0.0, home.stock_held(EGGS))
_ok, _why = home.start_reason("tx2_silk_fibre")
check("without the eggs the first silk node is refused, naming the eggs",
      not _ok and EGGS in (_why or ""), _why)
check("...and the refusal is a supply blocker naming no route",
      any(entry["kind"] == "supply" for entry in home.start_blockers("tx2_silk_fibre"))
      and not any("sea_monsoon_route" in entry["ids"] for entry in home.start_blockers("tx2_silk_fibre")),
      home.start_blockers("tx2_silk_fibre"))

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
han = unopened_sim(civ=PARTNER, capital=1e9)
check("the partner opens holding eggs", han.stock_held(EGGS) > 0.0, han.stock_held(EGGS))
check("so no node of its own is missing a stock",
      not han.stock_missing("tx2_sericulture") and not han.stock_missing("tx2_silk_fibre"), None)

# --- the partner's refusal is its state's decision: its export policy holds the monopoly back.
buyer = sim(civ=HOME, capital=1e9)
check("a partner that refuses to sell eggs sells none",
      buyer.buy_stock_from_partner(EGGS, 0.1, PARTNER) == 0.0 and buyer.stock_held(EGGS) == 0.0,
      buyer.stock_held(EGGS))
check("...and says so", cause_of(buyer.partner_refusal(PARTNER, EGGS)) == "partner_export_held_back",
      buyer.partner_refusal(PARTNER, EGGS))

# --- a partner that offers them: the purchase is paid for and opens the node.
buyer = sim(civ=HOME, capital=1e9)
seed_opening_cast(buyer)
buyer.partner_government(PARTNER).record.state_monopolies.clear()
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

# --- stock survives a save and load within a build.
from sim.engine.saveload import load_state, save_state
with tempfile.TemporaryDirectory() as _folder:
    _path = os.path.join(_folder, "save.json")
    save_state(buyer, _path)
    _revived = unopened_sim(civ=HOME, capital=1e9)
    load_state(_revived, _path)
check("held stock round-trips through save and load",
      abs(_revived.stock_held(EGGS) - buyer.stock_held(EGGS)) < 1e-12 and _revived.stock_held(EGGS) > 0.0,
      (_revived.stock_held(EGGS), buyer.stock_held(EGGS)))

# --- a draught-animal gate is lifted by holding the animals, however they came.
_mexica = unopened_sim(civ="mexica_1500", capital=1e9)
_gate, _because = _mexica.needs_first("horse_collar")
check("a society holding no draught animals is gated", _gate == "exp_import_draught_animals", _gate)
_mexica.grant_stock("draught_animal_kg", 2000.0)
check("holding draught animals lifts the gate with no research",
      _mexica.needs_first("horse_collar")[0] is None, _mexica.needs_first("horse_collar"))

# --- one crop seed stock: ramie propagation stock, held by the partner, bought by others.
check("the partner opens holding ramie stock",
      unopened_sim(civ=PARTNER).stock_held("ramie_stock_kg") > 0.0, None)

# the module-level patch above is undone so later topics in this process see the shipped records
_foreign_module.foreign_economy_records = _shipped_records
