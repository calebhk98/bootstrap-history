"""failure_and_bounty_money: complaints 247 and 214 (the failure charge is the
quoted figure, from the bill the player actually bears), 248 (a failed bounty
is not orphaned) and 249 (selling stock faces the market's limits)."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.techtree import _explain_timing_and_risk


class _ForcedDraw(random.Random):
    def __init__(self, forced_draw):
        super().__init__(1)
        self.forced_draw = forced_draw

    def random(self):
        return self.forced_draw


def _quote(test_sim, node_id):
    return _explain_timing_and_risk(test_sim, NODES, node_id, NODES[node_id])["failure_costs"]


def _fail_and_measure(test_sim, node_id):
    """Start the project, force the roll to fail, return the cash it cost."""
    test_sim.rng = _ForcedDraw(0.0)
    test_sim.initialize_project(node_id)
    before = test_sim.capital
    test_sim._complete(node_id)
    return before - test_sim.capital


_NODES_TO_FAIL = ("blast_furnace", "mat_bulk_steel", "zinc_industry_scale")

# --- 251 / 218: the charge is the quote, whatever is held or already bought ---
for _node_id in _NODES_TO_FAIL:
    check("set-up: %s exists and can fail" % _node_id,
          _node_id in NODES and NODES[_node_id]["risk"] > 0, _node_id)
    _empty = sim(capital=1e10)
    _empty_quote = _quote(_empty, _node_id)
    _empty_lost = _fail_and_measure(_empty, _node_id)
    check("%s: nothing held, the charge equals the quote" % _node_id,
          abs(_empty_lost - _empty_quote) <= 0.01 * max(1.0, _empty_quote),
          (_empty_lost, _empty_quote))

    _stocked = sim(capital=1e10)
    for _row in _stocked.project_material_bill(_node_id)["rows"]:
        _stocked.buy_material_stock(_row["material"], _row["missing_tonnes"])
    _stocked_quote = _quote(_stocked, _node_id)
    _stocked_lost = _fail_and_measure(_stocked, _node_id)
    check("%s: materials held in stock, the charge equals the quote" % _node_id,
          abs(_stocked_lost - _stocked_quote) <= 0.01 * max(1.0, _stocked_quote),
          (_stocked_lost, _stocked_quote))
    check("%s: holding the materials does not make a failure cost more" % _node_id,
          _stocked_lost <= _empty_lost * 1.001, (_stocked_lost, _empty_lost))

# the quote is also right once the project is running (the bill is frozen)
_running = sim(capital=1e10)
_running.rng = _ForcedDraw(0.0)
_running.initialize_project("blast_furnace")
_running_quote = _quote(_running, "blast_furnace")
_running_before = _running.capital
_running._complete("blast_furnace")
check("a running project's quote is what its failure then charges",
      abs((_running_before - _running.capital) - _running_quote) <= 0.01 * max(1.0, _running_quote),
      (_running_before - _running.capital, _running_quote))

# 218: a civilisation with a cost factor, and an opposed node
_han = sim(civ="han_china_100ad", capital=1e10)
_han_node = next(node_id for node_id in ORDER
                 if node_id not in _han.done and NODES[node_id]["risk"] > 0
                 and _han.civ_cost_factor(node_id) < 0.9)
_han_quote = _quote(_han, _han_node)
_han_lost = _fail_and_measure(_han, _han_node)
check("a civilisation with a cost multiplier: charge equals quote",
      abs(_han_lost - _han_quote) <= 0.01 * max(1.0, _han_quote), (_han_node, _han_lost, _han_quote))

# --- 252: a failed bounty is neither charged to the poster nor orphaned ------
_bounty_sim = sim(capital=5e7)
_bounty_id = "horse_collar"
_posted = _bounty_sim.post_bounty(_bounty_id)
check("set-up: the bounty was posted", _posted)
_bounty_sim.rng = _ForcedDraw(0.0)
_cash_before = _bounty_sim.capital
_bounty_sim._complete(_bounty_id)
check("a failed bounty does not charge the poster a second time",
      abs(_bounty_sim.capital - _cash_before) < 1e-6, _cash_before - _bounty_sim.capital)
_record = _bounty_sim.active.get(_bounty_id)
check("the failed bounty is still active", _record is not None)
check("it is still the claimant's work: no hours land on the poster",
      _bounty_id in _bounty_sim.bountied and _record["ph_left"] == 0, _record)
check("the attempt is counted and part of the calendar is banked",
      _bounty_sim.failed_attempts[_bounty_id] == 1)
check("the log says the claimant failed and the prize holds",
      any("claimant" in text and "prize" in text
          for _year, text in _bounty_sim.state.household.log[-3:]),
      _bounty_sim.state.household.log[-3:])
_bounty_sim.rng = _ForcedDraw(0.999999)
for _year_index in range(40):
    if _bounty_id in _bounty_sim.done:
        break
    _bounty_sim.step()
check("a failed bounty finishes on a later attempt", _bounty_id in _bounty_sim.done,
      _bounty_sim.active.get(_bounty_id))

# --- 253: selling stock faces the same market limits as buying ----------------
_sell = sim(capital=5e7)
_quote = _sell.material_trade_quote("coal")
_absorbed = _quote["market_available_tonnes_per_year"]
_sell._material_stock()["coal"] += 50 * _absorbed
_sell._material_opening_stock()["coal"] = _sell.material_stock_t("coal")
_cash = _sell.capital
_sold_small = _sell.sell_material_stock("coal", 1.0)
_small_price = _sell.capital - _cash
check("a one tonne sale is paid at about the quoted sell price",
      _sold_small == 1.0 and abs(_small_price - _quote["sell_per_tonne"]) < 0.02 * _quote["sell_per_tonne"],
      (_small_price, _quote["sell_per_tonne"]))
_cash = _sell.capital
_sold_big = _sell.sell_material_stock("coal", 40 * _absorbed)
check("a sale is cut to what the market absorbs in a year", _sold_big <= _absorbed + 1e-6,
      (_sold_big, _absorbed))
_big_average = (_sell.capital - _cash) / max(_sold_big, 1e-9)
check("selling a year's market at once pays less per tonne than one tonne",
      _big_average < 0.9 * _small_price, (_big_average, _small_price))
_cash = _sell.capital
_sold_more = _sell.sell_material_stock("coal", _absorbed)
check("selling more in the same year is cut to nothing or to a lower price",
      _sold_more < 1e-6 or (_sell.capital - _cash) / _sold_more < _big_average,
      (_sold_more, _sell.capital - _cash))
