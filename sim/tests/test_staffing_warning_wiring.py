"""What the game feeds the staffing warning (`StaffingMixin.staffing_closure_warnings` gathers the household's numbers for
`staffing_warning_rows`, replaced here by a recorder) and that the state screen shows a warning row (a dict) as its sentence
and not as the dict (a TypeError once swallowed the whole annual report). The rows' arithmetic is in test_staffing_warnings;
the sentences are `_staffing_warning_sentences`. Both run on stand-ins."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

from sim.engine import projects_staffing
from sim.engine.projects_staffing import StaffingMixin
from sim.ui.proto.render_screen_state_blocks import _state_founder

NODES = {"b_mill": {"name": "Mill", "rev": 900.0, "up": 300.0}, "a_forge": {"name": "Forge", "rev": 500.0, "up": 100.0}}


class Game(StaffingMixin):
    """The parts of a Sim the warning reads."""
    FOUNDER_IS_WORTH = 1.0
    STAFFING_CLOSURE_SLACK = 0.5
    STAFFING_WARNING_BAND = 5.0
    STAFFING_NO_SLACK_BAND = 1.0
    STAFF_SOURCES = {"artisan": [("other", "no"), ("HIRE", "hire an artisan")]}
    nodes = NODES

    def __init__(self, operating=("b_mill", "a_forge"), founder_alive=True, immortal=False):
        self.state = SimpleNamespace(
            projects=SimpleNamespace(operating=set(operating)),
            household=SimpleNamespace(artisans=30.0, scholars=4.0),
            founder=SimpleNamespace(founder_alive=founder_alive))
        self.cfg = {"immortal": immortal}
        self.labour = SimpleNamespace(effective_scholars=lambda: 7.5)

    def venture_staff_used(self):
        return 2.0, 25.0

    def venture_hands(self, node_id):
        return {"b_mill": (1.0, 3.0), "a_forge": (0.0, 2.0)}[node_id]


def warnings(game, **keywords):
    with mock.patch.object(projects_staffing, "staffing_warning_rows", return_value=["rows"]) as rows:
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
