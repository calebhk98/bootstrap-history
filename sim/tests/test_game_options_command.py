"""The game_options command sets and lists dashboard_history_years, on a stand-in game holding only the seat progress."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto.dispatch_game_options import _cmd_game_options

game = SimpleNamespace(state=SimpleNamespace(seat_progress=SimpleNamespace(dashboard_history_years=None)))
reply = _cmd_game_options(game, {}, {"cmd": "game_options", "set": {"dashboard_history_years": 10}}, None)
check("setting dashboard_history_years stores the integer and the reply lists it",
      reply["ok"] and game.state.seat_progress.dashboard_history_years == 10 and reply["game_options"] == {"dashboard_history_years": 10}
      and reply["changed"] == {"dashboard_history_years": 10}, reply)
reply = _cmd_game_options(game, {}, {"cmd": "game_options"}, None)
check("without set the current value is listed and nothing changes",
      reply["game_options"] == {"dashboard_history_years": 10} and reply["changed"] == {}, reply)
reply = _cmd_game_options(game, {}, {"cmd": "game_options", "set": {"dashboard_history_years": "off"}}, None)
check("'off' clears the cap", reply["ok"] and game.state.seat_progress.dashboard_history_years is None, reply)
reply = _cmd_game_options(game, {}, {"cmd": "game_options", "set": {"dashboard_history_years": -3}}, None)
check("a non-positive cap is refused and leaves the option alone", reply["ok"] is False and game.state.seat_progress.dashboard_history_years is None, reply)
reply = _cmd_game_options(game, {}, {"cmd": "game_options", "set": {"no_such_option": 1}}, None)
check("an unknown option is refused", reply["ok"] is False, reply)
