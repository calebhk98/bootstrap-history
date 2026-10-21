"""SCENARIO (Complaint 640): The founder's job on a whole Rome game (Complaint 518): the income line is the unspoken-for hours times the
market wage of the trade the founder holds, and it moves with that wage and with the hours supervising take."""
from .harness import *  # noqa: F401,F403

game = sim()
trade = game.held_trade()
check("the founder holds a trade to sell", trade is not None, trade)

hours = game.labour.hours_for_sale()
pay = game.labour.wage_for_hours(trade, hours)
output_factor = game.state.economy.output_factor
check("the founder's job pays the hours sold times the market wage of the trade",
      hours > 0 and pay > 0 and abs(game.founder_wage_income() - pay) < 1e-6 * pay, (hours, pay, game.founder_wage_income()))
check("it shows as one income line, the wages of the founder's own work, and no practice line",
      abs(game.revenue_sources().get("_wages_for_your_own_work", 0.0) - round(pay * output_factor, 1)) < 0.11
      and "_your_own_practice" not in game.revenue_sources(), game.revenue_sources())
check("the practice income and its displacement are gone from the engine",
      not hasattr(game, "practice_income") and not hasattr(game.labour, "practice_income_displaced"), None)

# the wage moves: leaning on the trade raises its quote, and the founder's income follows
revenue_before = game.revenue()
game.labour.labour_market.press(trade, hours)
dearer_pay = game.labour.wage_for_hours(trade, hours)
check("the trade's wage rose when its labour was leaned on", dearer_pay > pay, (pay, dearer_pay))
check("the founder's income follows the wage",
      abs(game.founder_wage_income() - dearer_pay) < 1e-6 * dearer_pay, (game.founder_wage_income(), dearer_pay))
check("...and so does revenue", game.revenue() > revenue_before, (game.revenue(), revenue_before))
game.labour.labour_market.clear_pressure()

# hours supervising are hours not sold, one for one
revenue_free = game.revenue()
supervised = hours / 4.0
game.state.household.supervision_hours_this_year = supervised
check("supervising hours reduce hours sold one for one",
      abs(game.labour.hours_for_sale() - (hours - supervised)) < 1e-9, (game.labour.hours_for_sale(), hours, supervised))
check("...and the income by those hours at the trade's wage",
      abs(game.founder_wage_income() - game.labour.wage_for_hours(trade, hours - supervised)) < 1e-6 * pay,
      game.founder_wage_income())
check("...and revenue (the cached figure) sees the change", game.revenue() < revenue_free, (game.revenue(), revenue_free))
game.state.household.supervision_hours_this_year = 0.0

# a trade nobody hires pays what the market quotes for it, like any worker
game.held_trade = lambda: "scribe"
scribe_quote = game.labour.labour_market.quote_annual("scribe") / game.HOURS_PER_PERSON_YEAR
check("a founder whose trade nobody hires earns the market's quote for it (the reputation bonus is a rule in test_complaint_585_staff_pay_retention)",
      abs(game.founder_wage_income() - game.labour.wage_for_hours("scribe", hours)) < 1e-6 * max(1.0, pay)
      and game.labour.wage_for_hours("scribe", hours) > 0.0, (game.founder_wage_income(), scribe_quote))

# selling hours in another trade takes them out of the standing job, and nothing is charged as a lost practice
fresh = sim()
fresh_trade = fresh.held_trade()
standing_before = fresh.founder_wage_income()
sold_pay, _message = fresh.labour.work_for_wages("scribe", 500)
check("hours sold for wages come out of the standing job at the standing trade's wage",
      abs((standing_before - fresh.founder_wage_income()) - fresh.labour.wage_for_hours(fresh_trade, 500)) < 1e-6 * standing_before,
      (standing_before, fresh.founder_wage_income()))
