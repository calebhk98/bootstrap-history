"""failure_and_bounty_money: complaints 247 and 214 (the failure charge is the
quoted figure, from the bill the player actually bears), 248 (a failed bounty
is not orphaned) and 249 (selling stock faces the market's limits)."""
from .harness import *  # noqa: F401,F403
from sim.agents import borrowing_arrears
from sim.refusal import cause_of, facts_of
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


_NODES_TO_FAIL = ("blast_furnace",)

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

# 438: a failure cannot take the purse past the credit limit; what the purse cannot bear is billed to the project to redo
_capped = sim(capital=1e10)
_capped.rng = _ForcedDraw(0.0)
_capped.initialize_project("blast_furnace")
_loss = _capped.failure_loss("blast_furnace")
_capped.capital = 0.0
_capped.capital = -_capped.credit_limit() + 0.1 * _loss
_room_before = _capped.capital + _capped.credit_limit()
_owed_before = _capped.active["blast_furnace"]["cost_left"]
check("set-up: the failure is larger than the room left", 0 <= _room_before < _loss, (_room_before, _loss))
_capital_before = _capped.capital
_capped._complete("blast_furnace")
_borne = _capital_before - _capped.capital   # the line is read at the capital left, so the room is a little under _room_before
check("a failure never takes capital past the credit limit",
      _capped.capital >= -_capped.credit_limit() - 1e-6, (_capped.capital, _capped.credit_limit()))
check("the part of a failure the purse could not bear is added to what the project still costs",
      abs((_capped.active["blast_furnace"]["cost_left"] - _owed_before) - (_loss - _borne)) <= 1e-6 * _loss
      and _borne <= _room_before + 1e-6,
      (_capped.active["blast_furnace"]["cost_left"] - _owed_before, _loss - _borne))

# 438: the yearly charge for guarding coin is paid from the room under the credit limit, not past it
_guarded = sim(capital=1e6)
_guarded.coin_hoard = lambda: {"keeping_cost_per_year": 1e12}
_guarded_flows = []
_guarded_credit = _guarded.state.household.credit
_guarded.state.household.credit = lambda amount, purpose: (_guarded_flows.append(amount), _guarded_credit(amount, purpose))[1]
_guarded_room = _guarded.capital + _guarded.credit_limit()
_guarded._step_money()
check("the year's money flow, coin guard included, stays inside the room under the credit limit",
      _guarded_flows[0] >= -_guarded_room - 1e-6, (_guarded_flows[0], _guarded_room))

# 438, restated by 589: what the year's later phases (the state's levy, the market) take past the credit limit is not
# clamped; it stays as arrears, bounded by what was spent, and the lenders default it after ARREARS_YEARS_BEFORE_DEFAULT years
_levied = sim(capital=0.0, manual=True)
_levied.market_rate = lambda: 0.08   # arrears are unpaid interest, and a settled market may clear at a rate of zero
_levy_step_market = _levied._step_market
_late_spent = []
def _levy_past_the_limit():
    _levy_step_market()
    if not _late_spent:
        _late_spent.append(_levied.capital + _levied.credit_limit() + 1e5)
        _levied.state.household.debit(_late_spent[0], "requisition")
_levied._step_market = _levy_past_the_limit
_levied.step()
_past_the_limit = -_levied.capital - _levied.credit_limit()
check("a year's late spending past the credit limit is carried as a debt past it, no more than was spent",
      0.0 < _past_the_limit <= _late_spent[0] + 1e-6, (_past_the_limit, _late_spent[0]))
_arrears_years = []
for _year in range(borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT):
    _levied.step()
    _arrears_years.append(_levied.state.household.arrears_years)
check("the debt is arrears: each year it stays unpaid counts one more, until the lenders default it",
      _arrears_years[:-1] == list(range(1, borrowing_arrears.ARREARS_YEARS_BEFORE_DEFAULT)), _arrears_years)
check("...and in the stated year the default settles it, leaving capital inside the credit limit",
      _arrears_years[-1] == 0 and _levied.capital >= -_levied.credit_limit() - 1e-6
      and any(line.kind == "insolvency_settled" for _, line in _levied.state.household.log if hasattr(line, "kind")),
      (_arrears_years, _levied.capital, _levied.credit_limit()))

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
      any(cause_of(text) == "project_failed" and facts_of(text)["severity"] == "claimed"
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
# the fall is the economy's own: its book cleared again with the tonnes sold as one more offer (stage 3 of Complaint 507);
# how deep that is follows how many tonnes the engine's year of market is until stage 4 reads the offered quantity there
_fall = _sell.economy.agent_price_response(_sell.goods_market._economy_good("coal"), _sold_big, 0.0, _sell.economy.acting_tile())
check("selling a year's market at once pays less per tonne than one tonne",
      _big_average < _small_price, (_big_average, _small_price))
check("...and no less than the economy's price after all of it is on offer",
      _fall is not None and _big_average >= _small_price * _fall * (1.0 - 1e-3), (_big_average, _small_price, _fall))
_cash = _sell.capital
_sold_more = _sell.sell_material_stock("coal", _absorbed)
check("selling more in the same year is cut to nothing or to a lower price",
      _sold_more < 1e-6 or (_sell.capital - _cash) / _sold_more < _big_average,
      (_sold_more, _sell.capital - _cash))
