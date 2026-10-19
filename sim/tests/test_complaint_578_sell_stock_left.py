"""Complaints/578: `sell` reports the holding the next sale draws on, and refuses a sale of more than is held."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of
from .agent_command_helpers import ask_agent

_game = sim(capital=300000.0)
_key = _game.goods_market.quote("iron")["stock_key"]
_game.goods_market.acting.take_delivery(_key, 3000.0)

_first = ask_agent(_game, cmd="sell", material="iron", n=400)
_held_now = _game.goods_market.sale_limits("iron")[0]
check("the reply's stock left is the holding the market draws on",
      _first["stock_on_hand_tonnes"] == _held_now, (_first, _held_now))

_second = ask_agent(_game, cmd="sell", material="iron", n=100000)
check("selling more than is held is refused", _second["ok"] is False, _second)
check("the refusal's cause is not_enough_held",
      cause_of(_second["error"]) == "not_enough_held", _second)
check("the refusal states the quantity held",
      facts_of(_second["error"])["held_tonnes"] == _held_now, _second)

_room = _first["market_will_still_take_tonnes"]
_third = ask_agent(_game, cmd="sell", material="iron", n=_held_now)
check("the next sale sells what the reply said the market would still take",
      abs(_third["sold_tonnes"] - min(_room, _held_now)) < 1e-6, (_first, _third))
