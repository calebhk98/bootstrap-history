"""Scenario, Complaints 358 and 356: in a running game the founder's household, a firm, the state and an interest group
are all quoted the market's rate, and the hire quote is what payroll then charges. The market's own arithmetic is in
test_one_labour_market."""
from .harness import *  # noqa: F401,F403

from sim.engine.agents_port import SimWorld
from sim.ui.proto.quote_spending import _quote_hire

TRADE = "artisan"


def stressed_game():
    """A game with a non-unit price level, a non-unit demographic wage index and a scarcity premium."""
    game = unopened_sim()
    game.price_index = 1.5
    game._wage_index_base = 1.3
    game.labour.market.press(TRADE, game.labour.market_supply(TRADE) * 0.8)
    game.labour.market.press("labourer", game.labour.market_supply("labourer") * 0.8)
    game.labour.market.press("scribe", game.labour.market_supply("scribe") * 0.8)
    return game


game = stressed_game()
market = game.labour.market
hours_per_year = game.HOURS_PER_PERSON_YEAR
game.state.household.employees = {TRADE: 1.0}
rate = market.quote(TRADE, 0.0)
world = SimWorld(game)
node_id = next(node_id for node_id in game.nodes if game.is_venture(node_id) and "artisan" in world.concern_staff(node_id))
expected_bill = world.span_factor(1.0) * sum(people * hours_per_year * market.quote(staffed_trade)
                                             for staffed_trade, people in world.concern_staff(node_id).items())
labourer_year = market.quote("labourer") * hours_per_year
check("the founder's household, the state, a firm and an interest group all read the one market's rate",
      market.price_factor(TRADE) > 1.05 and game.price_index > 1.4 and game.wage_index > 1.2
      and abs(game.labour.wage_bill() / hours_per_year - rate) < 1e-9 * rate
      and world.labour_market is market
      and abs(world.pay_per_person_year(TRADE) - rate * hours_per_year) < 1e-9 * rate * hours_per_year
      and abs(world.concern_wage_bill(node_id) - expected_bill) < 1e-6 * expected_bill
      and abs(world._annual_labourer_wage() - labourer_year) < 1e-9 * labourer_year,
      (game.labour.wage_bill() / hours_per_year, rate, world.pay_per_person_year(TRADE) / hours_per_year,
       world.concern_wage_bill(node_id), expected_bill, world._annual_labourer_wage(), labourer_year))

hiring = stressed_game()
hiring.state.household.employees = {}
fee_quoted = hiring.labour.market.quote_annual(TRADE)
quote = _quote_hire(hiring, hiring.nodes, {"trade": TRADE, "n": 1})
ok, _message = hiring.labour.hire(TRADE, 1)
payroll_per_year = hiring.labour.wage_bill() / hiring.state.household.employees[TRADE]
check("the hire quote answers; its wage from next year is what payroll charges once hired, and its fee the first year's wage",
      quote.get("ok") and abs(quote["from_next_year_per_year"] - payroll_per_year) < 0.1
      and abs(quote["paid_now"] - fee_quoted) < 0.1,
      (quote, payroll_per_year, fee_quoted))
