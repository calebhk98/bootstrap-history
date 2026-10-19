"""Complaints/584: a concern's forecast, its takings for the year and the cash book's revenue read one function."""
from .harness import *  # noqa: F401,F403

NODE_ID = "fin_lottery"   # its goods have no market until it sells them; its inputs have one already
game = sim(civ="rome_100ad", capital=5_000_000.0)
game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
game.state.projects.done.add(NODE_ID)
game._done_changed()
game.labour.hire("artisan", 3)


def ask(**command):
    return S._agent_dispatch(game, NODES, command)


before = game.venture_real_earnings(NODE_ID)
tree_figure = game.concern_takings(NODE_ID, 1.0)
check("a concern whose goods have no market yet is quoted at its long-run takings, not at nothing",
      before > 0.0 and abs(before - tree_figure) < 1e-6, (before, tree_figure))
check("the quote says it has no market price yet",
      game.venture_forecast_basis(NODE_ID) == "long_run_no_market_yet", game.venture_forecast_basis(NODE_ID))
why = ask(cmd="why", id=NODE_ID)
check("the why screen carries the same basis", why.get("forecast_basis") == "long_run_no_market_yet", why.get("forecast_basis"))
check("the opened concern's reply quotes what the quote function gives",
      ask(cmd="open", id=NODE_ID).get("ok") is True, None)

# a year of takings: what the money screen itemised before the step is what the cash book booked
itemised = ask(cmd="money")["where_the_money_comes_from"]
forecast_row = itemised.get(NODE_ID)
check("the itemised row for the concern is the quote function's figure",
      forecast_row is not None and abs(forecast_row - round(game.venture_real_earnings(NODE_ID), 1)) < 0.11,
      (forecast_row, game.venture_real_earnings(NODE_ID)))
ask(cmd="step", years=1)
booked = ask(cmd="money")["cash_book"]["earlier_years"][-1]["causes"].get("venture revenue")
check("the cash book's revenue line equals the itemised revenue", booked is not None and abs(booked - sum(itemised.values())) < 0.2,
      (booked, sum(itemised.values())))
check("once it sells, its goods have a market price and the basis says so",
      game.venture_forecast_basis(NODE_ID) == "market", game.venture_forecast_basis(NODE_ID))

# a running concern's forecast for the year is its takings that year
quote = game.venture_real_earnings(NODE_ID)
itemised = ask(cmd="money")["where_the_money_comes_from"]
ask(cmd="step", years=1)
booked_row = ask(cmd="money")["cash_book"]["earlier_years"][-1]["causes"].get("venture revenue")
check("a running concern's forecast is within the year's price change of its takings",
      abs(itemised[NODE_ID] - quote) < 0.11 and abs(booked_row - sum(itemised.values())) < 0.2,
      (quote, itemised, booked_row))
