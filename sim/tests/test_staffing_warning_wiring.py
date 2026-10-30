"""What the game feeds the staffing warning (the projects module's `staffing_closure_warnings` gathers the household's numbers for
`staffing_warning_rows`, replaced here by a recorder) and that the state screen shows a warning row (a dict) as its sentence
and not as the dict (a TypeError once swallowed the whole annual report). The rows' arithmetic is in test_staffing_warnings;
the sentences are `_staffing_warning_sentences`. The module runs over plain values."""

QUICK_TOPIC = True

from unittest import mock

from .harness import check

from sim.projects import staffing
from sim.tests import projects_host
from sim.ui.proto.render_screen_state_blocks import _state_founder

NODES = {"b_mill": {"name": "Mill", "rev": 900.0, "up": 300.0}, "a_forge": {"name": "Forge", "rev": 500.0, "up": 100.0}}


def Game(operating=("b_mill", "a_forge"), founder_alive=True, immortal=False):
    """The projects module with what the warning reads."""
    return projects_host.build(
        tree=NODES, operating=lambda: set(operating), staff={"artisans": 30.0, "scholars": 4.0, "employees": {}},
        founder={"alive": founder_alive, "life_left": 10.0, "dead_reason": None, "policy": {}}, game_config={"immortal": immortal},
        effective_scholars=7.5, venture_staff_used=lambda: (2.0, 25.0),
        venture_hands=lambda node_id: {"b_mill": (1.0, 3.0), "a_forge": (0.0, 2.0)}[node_id],
        staff_sources=lambda: {"artisan": [("other", "no"), ("HIRE", "hire an artisan")]})


def warnings(game, **keywords):
    with mock.patch.object(staffing, "staffing_warning_rows", return_value=["rows"]) as rows:
        result = game.staffing_closure_warnings(**keywords)
    return result, rows


result, rows = warnings(Game())
(concerns, scholars_held, craftsmen_held, hired_scholars, hired_craftsmen, scholars_used, craftsmen_used, founder_fixed,
 slack, band, no_slack_band, limit, fix_for, money_for) = rows.call_args.args
check("the rows are what the rule returns", result == ["rows"], result)
check("the concerns are the running ones in id order with their tree figures and hands",
      concerns == [{"id": "a_forge", "name": "Forge", "revenue": 500.0, "upkeep": 100.0, "hands": (0.0, 2.0)},
                   {"id": "b_mill", "name": "Mill", "revenue": 900.0, "upkeep": 300.0, "hands": (1.0, 3.0)}], concerns)
check("the household's scholars, its craftsmen plus the founder, and the hired of each are handed in",
      (scholars_held, craftsmen_held, hired_scholars, hired_craftsmen) == (7.5, 31.0, 4.0, 30.0),
      (scholars_held, craftsmen_held, hired_scholars, hired_craftsmen))
check("the staff the concerns use are handed in", (scholars_used, craftsmen_used) == (2.0, 25.0))
check("the slack, the warning band, the no-slack band and the limit are the game's",
      (slack, band, no_slack_band, limit) == (0.5, 5.0, 1.0, 3), (slack, band, no_slack_band, limit))
check("the fix for a kind of staff is the game's hire route", fix_for("artisan") == "hire an artisan")
check("a founder who can die leaves the hired people at risk, so he is not fixed", founder_fixed is False)
check("an immortal founder is fixed", warnings(Game(immortal=True))[1].call_args.args[7] is True)
dead_founder_arguments = warnings(Game(founder_alive=False))[1].call_args.args
check("a dead founder adds nothing to the craftsmen and is fixed",
      (dead_founder_arguments[2], dead_founder_arguments[7]) == (30.0, True), dead_founder_arguments)
check("a limit asked for is passed on", warnings(Game(), limit=1)[1].call_args.args[11] == 1)
nothing, none_called = warnings(Game(operating=()))
check("no running concern gives no warning and asks the rule nothing", nothing == [] and none_called.call_count == 0)

warning = {"id": "a_forge", "name": "Forge", "of": "craftsmen", "within": 0.5, "one_loss_closes_it": True,
           "headline": "Forge: losing one more craftsman closes it"}
reply = {"founder_alive": True, "founder_ages": True, "founder_age": 40, "founder_hours_available": 300.0,
         "supervision_close_to_the_edge": [warning]}
lines = _state_founder(reply)
check("the state screen's founder block shows a warning row as its headline",
      all(isinstance(line, str) for line in lines) and any("Forge: losing one more craftsman closes it" in line for line in lines), lines)
check("a state with no warning shows none", not any("Forge" in line for line in _state_founder(dict(reply, supervision_close_to_the_edge=None))))
