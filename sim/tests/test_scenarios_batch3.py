"""SCENARIO (Complaint 640): Complaint 640, audit batch 3: the scenarios the rule tests leave to a whole game.

Each rule that used to be checked here through a game is now a test of its own function (the files named in each
scenario's comment). What stays is wiring: that the screens, the commands and the engine call the one function, and
that a save, a year and a purchase hold together. One scenario per subject, each a named block below."""
from unittest import mock

from .harness import *  # noqa: F401,F403
from .harness import _mk_loom_sim
from sim.engine.data import closure as _closure
from sim.refusal import cause_of, facts_of
from sim.ui.proto.typed import parse_typed
from .agent_command_helpers import ask_agent


def _run(sim_state, text):
    parsed, error = parse_typed(text)
    if error:
        return {"ok": False, "error": error}
    return S._agent_dispatch(sim_state, NODES, parsed)


def _close(left, right):
    return left is not None and right is not None and abs(left - right) < 0.06


# ---- scenario: the room advice and `quote housing` price a place alike; the hire refusal carries the advice -------
# rules: test_complaint_163_room_advice_housing
_room_game = unopened_sim(capital=1000000.0)
_room_advice = _room_game.labour._room_advice()
_hired, _hire_refusal = _room_game.labour.hire("smith", 20)
_housing_quote = _run(_room_game, "quote housing 10")
check("scenario room advice: the advice prices a place as `quote housing` does",
      _housing_quote["per_unit"] == round(_room_game.housing_price_per_place(), 2)
      and ("%.0f" % _room_game.housing_price_per_place()) in _room_advice.replace(",", ""),
      (_housing_quote.get("per_unit"), str(_room_advice)))
check("scenario room advice: the hire refusal has the advice's remedies, housing first",
      not _hired and cause_of(_hire_refusal) == "household_room"
      and facts_of(_hire_refusal)["remedies"] == facts_of(_room_advice)["remedies"]
      and facts_of(_hire_refusal)["remedies"][0]["action"] == "buy_housing", _hire_refusal)


# ---- scenario: the engine's quoted wage of a trade is the economy api's weighted wage in coin -----------------
# rules: test_complaint_394_weighted_wage_quote
from sim.economy import api as _economy_api
_wage_game = sim()
_wage_agent = _wage_game.economy.agent
_wage_economy = _wage_agent.economy()
_wage_coin = _wage_economy.setup.coin_per_unit
_wage_agent._answers = None
_quoted_wages = _wage_agent.answers()[1]
_api_wages = _economy_api.wages_by_trade_weighted(_wage_economy)
check("scenario wage quote: the engine's quote of every trade is the api's weighted wage in coin",
      bool(_quoted_wages) and set(_quoted_wages) == set(_api_wages)
      and all(abs(_quoted_wages[trade] - _api_wages[trade] * _wage_coin) < 1e-9 for trade in _api_wages),
      (_quoted_wages, _api_wages))


# ---- scenario: every quoted affordable amount of a purchase is bought in full ----------------------------------
# rules: test_complaint_59_quote_matches_purchase
from sim.ui.proto.dispatch_money import _cmd_quote
_LITTLE_CASH = 3000.0   # little cash, so a quoted figure that counted credit would differ from cash alone


def _quoted(quote_cmd):
    game = sim(capital=_LITTLE_CASH)
    return game, _cmd_quote(game, NODES, quote_cmd, None)


_forest_game, _forest_quote = _quoted({"what": "forest", "n": 100})
check("scenario quote and purchase: the quoted hectares of forest are bought in full",
      _forest_quote["you_can_afford_about"] > 0
      and _forest_game.buy_forest(_forest_quote["you_can_afford_about"]) == _forest_quote["you_can_afford_about"],
      _forest_quote)
_nitre_game, _nitre_quote = _quoted({"what": "nitre_bed", "n": 10000})
check("scenario quote and purchase: the quoted square metres of nitre bed are laid in full",
      _nitre_quote["you_can_afford_about"] > 0
      and _nitre_game.build_nitre(_nitre_quote["you_can_afford_about"]) == _nitre_quote["you_can_afford_about"],
      _nitre_quote)
_mine_game, _mine_quote = _quoted({"what": "mine", "material": "coal", "n": 500})
check("scenario quote and purchase: the quoted tonnage of mine is sunk in full",
      _mine_quote["you_can_afford_about"] > 0
      and _mine_game.open_mine("coal", _mine_quote["you_can_afford_about"], partial=False)
      == _mine_quote["you_can_afford_about"], _mine_quote)
# a few people cost more than the little cash buys, so the cash is a multiple of one person's price (in the same
# units the little cash is quoted in), and the quote is asked again
_one_person = _quoted({"what": "slaves", "n": 1})[1]
_slaves_cash = _LITTLE_CASH * 10 * _one_person["per_person_base"] / _one_person["you_have"]
_slaves_game = sim(capital=_slaves_cash)
_slaves_quote = _cmd_quote(_slaves_game, NODES, {"what": "slaves", "n": 100}, None)
check("scenario quote and purchase: the slaves quote shows the shared budget and the people are bought in full",
      "you_could_raise" in _slaves_quote and _slaves_quote["you_can_afford_about"] > 0
      and _slaves_game.labour.buy_slaves(_slaves_quote["you_can_afford_about"]) == _slaves_quote["you_can_afford_about"],
      _slaves_quote)
_over_game, _over_quote = _quoted({"what": "forest", "n": 100})
check("scenario quote and purchase: twice the quoted forest is refused",
      _over_game.buy_forest(_over_quote["you_can_afford_about"] * 2 + 1) == 0.0, _over_quote)
_refused = proto([{"cmd": "buy", "what": "forest", "n": 100000}])[0][0]
check("scenario quote and purchase: the buy refusal is the shared budget's cash_short",
      not _refused.get("ok") and _refused.get("cause") == "cash_short", _refused)
_stock_game = sim(capital=_LITTLE_CASH)
_material_quote = _stock_game.material_trade_quote("iron")
if _material_quote:
    _tonnes = min(_stock_game.spending_power("buy") / _material_quote["buy_per_tonne"] * 0.999,
                  _material_quote["market_available_tonnes_per_year"])
    # the price climbs as the order is filled, so the amount that fits the budget is the one whose bill does
    while _stock_game.material_purchase_cost("iron", _tonnes)[0] > 0.999 * _stock_game.spending_power("buy"):
        _tonnes *= 0.9
    check("scenario quote and purchase: an amount within the shared budget of material stock is bought in full",
          _stock_game.buy_material_stock("iron", _tonnes) == _tonnes, _tonnes)


# ---- scenario: every screen quotes a concern's earnings and upkeep from venture_real_earnings / _upkeep -----------
# rules: test_complaint_577_quote_is_takings (the arithmetic), test_complaint_584_forecast_takings_cash_book
# A saturated market (three looms), a trade-route bonus running, and a price level and output factor that make the
# tree's raw figure differ from the real one.
_crowded, _loom_ids = _mk_loom_sim(3, 60)
if "exp_trade_route_extend" in NODES:
    run_it(_crowded, "exp_trade_route_extend")
_crowded.price_index = 1.7
_crowded.output_factor = 0.9
_loom = _loom_ids[0]
_real_earnings = _crowded.venture_real_earnings(_loom)
_real_upkeep = _crowded.venture_real_upkeep(_loom)
check("scenario earnings figure: set-up, saturation and prices make the real figure differ from the tree's",
      abs(_real_earnings - NODES[_loom]["rev"]) > 1.0 and abs(_real_upkeep - NODES[_loom]["up"]) > 1.0,
      (_real_earnings, _real_upkeep, NODES[_loom]["rev"], NODES[_loom]["up"]))
_ventures_row = next(row for row in _run(_crowded, "ventures")["running"] if row["id"] == _loom)
_money = _run(_crowded, "money")
_why = _run(_crowded, "why " + _loom)
check("scenario earnings figure: ventures, money and why quote the same earnings and upkeep",
      _close(_ventures_row["earns_a_year"], _real_earnings) and _close(_ventures_row["costs_a_year"], _real_upkeep)
      and _close(_money["where_the_money_comes_from"].get(_loom), _real_earnings)
      and _close(_why.get("revenue"), _real_earnings) and _close(_why.get("upkeep"), _real_upkeep),
      (_ventures_row, _money["where_the_money_comes_from"].get(_loom), _why.get("revenue"), _why.get("upkeep"),
       _real_earnings, _real_upkeep))
check("scenario earnings figure: the ledger row of an open concern is the same figure",
      _loom not in _crowded.ledger_concern_rows()
      or abs(_crowded.ledger_concern_rows()[_loom] - _real_earnings) < 0.1, _crowded.ledger_concern_rows())
check("scenario earnings figure: an open concern's quote is what revenue() sums for it before the output factor",
      abs(_real_earnings - _crowded.concern_revenue(_loom) * _crowded.state.economy.output_factor) < 1e-6,
      (_real_earnings, _crowded.concern_revenue(_loom)))

# a concern not yet built: `available` and `why` agree with the same methods
_fresh = sim(capital=1_000_000)
_fresh.price_index = 1.7
_fresh.output_factor = 0.9
# a concern that earns once the market's price is applied, with everything it rests on known and on the list
_earners = sorted((node_id for node_id in NODES if _fresh.is_venture(node_id) and _fresh.venture_real_earnings(node_id) > 0),
                  key=lambda node_id: len(_closure(NODES, node_id)))
for _earner in _earners:
    _fresh.done.update(_closure(NODES, _earner) - {_earner})
    _fresh._done_changed()
    _listed = _run(_fresh, "available sort earns reverse limit 5")["available"]
    if any(row["earns_per_year"] > 0 for row in _listed):
        break
_candidate = next(row for row in _listed if row["earns_per_year"] > 0)
_candidate_why = _run(_fresh, "why " + _candidate["id"])
_candidate_earns = _fresh.venture_real_earnings(_candidate["id"])
_candidate_costs = _fresh.venture_real_upkeep(_candidate["id"])
check("scenario earnings figure: available and why quote an unbuilt concern at the same earnings, upkeep and net",
      _close(_candidate["earns_per_year"], _candidate_earns) and _close(_candidate["costs_per_year_after"], _candidate_costs)
      and _close(_candidate_why.get("revenue"), _candidate["earns_per_year"])
      and _close(_candidate_why.get("upkeep"), _candidate["costs_per_year_after"])
      and _close(_candidate.get("net_per_year"), _candidate_earns - _candidate_costs), (_candidate, _candidate_why))


# ---- scenario: a concern's forecast, its year's takings and the cash book's revenue read one function ----------------
# rules: test_complaint_584_forecast_takings_cash_book
_NODE = "fin_lottery"   # its goods have no market until it sells them; its inputs have one already
_book = sim(civ="rome_100ad", capital=5_000_000.0)
_book.end_year = _book.cfg["start_year"] + _book.cfg["horizon_years"]
_book.state.projects.done.add(_NODE)
_book._done_changed()
_book.labour.hire("artisan", 3)
# the founder's household is a payer in the coin-carriage hook, which reads `record.country`: its arrears book must not be its `record`
check("scenario cash book: the founder's household keeps its arrears in the household finances, not in a `record`",
      getattr(_book.household, "record", None) is None or hasattr(_book.household.record, "country"), None)
_forecast = _book.venture_real_earnings(_NODE)
check("scenario cash book: a concern whose goods have no market yet is quoted at its long-run takings and says so",
      _forecast > 0.0 and abs(_forecast - _book.concern_takings(_NODE, 1.0)) < 1e-6
      and _book.venture_forecast_basis(_NODE) == "long_run_no_market_yet"
      and ask_agent(_book, cmd="why", id=_NODE).get("forecast_basis") == "long_run_no_market_yet",
      (_forecast, _book.venture_forecast_basis(_NODE)))
ask_agent(_book, cmd="open", id=_NODE)
_itemised = ask_agent(_book, cmd="money")["where_the_money_comes_from"]
check("scenario cash book: the itemised row for the open concern is the quote function's figure",
      _itemised.get(_NODE) is not None and abs(_itemised[_NODE] - round(_book.venture_real_earnings(_NODE), 1)) < 0.11,
      (_itemised.get(_NODE), _book.venture_real_earnings(_NODE)))
ask_agent(_book, cmd="step", years=1)
_booked = ask_agent(_book, cmd="money")["cash_book"]["earlier_years"][-1]["causes"].get("venture revenue")
check("scenario cash book: the year's cash book revenue line equals the itemised revenue",
      _booked is not None and abs(_booked - sum(_itemised.values())) < 0.2, (_booked, sum(_itemised.values())))
check("scenario cash book: once it sells, its goods have a market price and the basis says so",
      _book.venture_forecast_basis(_NODE) == "market", _book.venture_forecast_basis(_NODE))
_quote = _book.venture_real_earnings(_NODE)
_itemised_again = ask_agent(_book, cmd="money")["where_the_money_comes_from"]
ask_agent(_book, cmd="step", years=1)
_booked_again = ask_agent(_book, cmd="money")["cash_book"]["earlier_years"][-1]["causes"].get("venture revenue")
check("scenario cash book: a running concern's forecast is within the year's price change of its takings",
      abs(_itemised_again[_NODE] - _quote) < 0.11 and abs(_booked_again - sum(_itemised_again.values())) < 0.2,
      (_quote, _itemised_again, _booked_again))


# ---- scenario: `sell` reports the holding and market room the next sale draws on, and refuses more than is held -----
# rules: test_complaint_578_sell_stock_left
_sale = sim(capital=300000.0)
_sale_key = _sale.goods_market.quote("iron")["stock_key"]
_sale.goods_market.acting.take_delivery(_sale_key, 3000.0)
_first_sale = ask_agent(_sale, cmd="sell", material="iron", n=400)
_held_now = _sale.goods_market.sale_limits("iron")[0]
check("scenario sell: the reply's stock left is the holding the market draws on",
      _first_sale["stock_on_hand_tonnes"] == _held_now, (_first_sale, _held_now))
_too_much = ask_agent(_sale, cmd="sell", material="iron", n=100000)
check("scenario sell: selling more than is held is refused with its cause and the quantity held",
      _too_much["ok"] is False and cause_of(_too_much["error"]) == "not_enough_held"
      and facts_of(_too_much["error"])["held_tonnes"] == _held_now, _too_much)
_third_sale = ask_agent(_sale, cmd="sell", material="iron", n=_held_now)
check("scenario sell: the next sale sells what the reply said the market would still take",
      abs(_third_sale["sold_tonnes"] - min(_first_sale["market_will_still_take_tonnes"], _held_now)) < 1e-6,
      (_first_sale, _third_sale))
