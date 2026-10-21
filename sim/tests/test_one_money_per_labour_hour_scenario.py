"""SCENARIO: a Rome game whose economy opens counts an hour of work at the economy's wage from then on, and reprices
its purse and tree. The rules (the figure in use, the purse ratio, the rebased tree) are in `test_one_money_per_labour_hour`."""
from .harness import *  # noqa: F401,F403

# The money an hour of work is worth is the agent economy's wage for the unskilled trade, once it has opened.
# Before it opens the opening's figure answers, and opening reprices what was counted at the opening's figure:
# the purse and the tree's money fields. Opening the economy spins it up, so this topic is slow.

_unopened = unopened_sim(civ="rome_100ad")
_opening_figure = _unopened.labour.money_per_labour_hour()
check("a game whose economy has not opened counts an hour at the opening's figure",
      _unopened.state.economy.money_from_economy is False and _opening_figure > 0.0, _opening_figure)

_game = unopened_sim(civ="rome_100ad")
_game.economy._opening = False     # the economy is left to open here, with the money counted at the opening's figure
_figure_before = _game.labour.money_per_labour_hour()
_purse_before = _game.state.household.capital
_node_id, _node = next((key, each) for key, each in _game.nodes.items() if each.get("cap_hours", 0.0) > 0.0)
_cap_hours = _node["cap_hours"]
_game.economy.open_agent()
_agent = _game.economy.agent
_unskilled = _agent.economy().setup.unskilled_trade
_economy_wage = _agent.wage_per_hour(_unskilled)
_figure = _game.labour.money_per_labour_hour()

check("the engine's money per labour hour is the economy's wage for the unskilled trade",
      abs(_figure - _economy_wage) <= 1e-12 * max(1.0, _economy_wage), (_figure, _economy_wage))
check("...and the economy's wage differs from the opening's figure, so the opening was repriced",
      abs(_figure - _figure_before) > 1e-6 * _figure_before, (_figure, _figure_before))
check("the founder's purse moved by the ratio of the figures, so it buys the hours it bought",
      abs(_game.state.household.capital / _figure - _purse_before / _figure_before) <= 1e-6 * _purse_before / _figure_before,
      (_game.state.household.capital, _purse_before, _figure, _figure_before))
_priced_node = _game.nodes[_node_id]
check("living costs are the need floors at the economy's prices, in the same coin",
      abs(_game.household_bill_per_person() - sum(_game.economy.agent_need_floor_costs_at().values())) <= 1e-9,
      _game.household_bill_per_person())

_game.step()
_after_year = _game.labour.money_per_labour_hour()
check("after a year it is still the economy's wage",
      abs(_after_year - _agent.wage_per_hour(_unskilled)) <= 1e-12 * max(1.0, _after_year),
      (_after_year, _agent.wage_per_hour(_unskilled)))
