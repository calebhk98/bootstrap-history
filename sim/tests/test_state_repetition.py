"""Complaint 100, items 9 and 10: the closing-concerns pointer explains itself once, and a long run of
active projects collapses to a bounded list plus a summary by what they wait on. Complaint 640: the once-only rule
(`already_explained`) is called on a stand-in game; the `state` command's use of it is test_state_command_explains_once."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto.explain_once import already_explained
from sim.ui.proto.render_screen_state_blocks import _state_concerns, _state_running
from sim.tests.ui_stand_in import Game


def stand_in_game():
    return Game(year=100, state=Game(acting_record=Game(seat_progress=Game(_said_explanations=None))))


game = stand_in_game()
check("a topic is not yet explained the first time it is shown", already_explained(game, "topic", {}) is False)
check("the second time it is already explained", already_explained(game, "topic", {}) is True)
check("`full` explains it again", already_explained(game, "topic", {"full": True}) is False)
check("and it stays explained for the next plain ask", already_explained(game, "topic", {}) is True)
check("another topic is separate", already_explained(game, "other", {}) is False)
check("the year the topic was first shown is kept", game.state.acting_record.seat_progress._said_explanations["topic"] == 100,
      game.state.acting_record.seat_progress._said_explanations)

first = {"concerns_you_run": 3, "you_know_how_to_run_but_have_not_opened": 5}
second = dict(first, shut_concerns_pointer_seen=True)
whole = "\n".join(_state_concerns(first))
brief = "\n".join(_state_concerns(second))
check("the whole line says what to do about shut concerns",  # presentation: wording of the pointer
      "have not opened them" in whole, whole)
check("the repeat is shorter and still points at 'ventures'",  # presentation: wording of the pointer
      len(brief) < len(whole) and "ventures" in brief and "have not opened them" not in brief, brief)

crowd = {"project_%02d" % number: {"founder_hours_total": 100, "founder_hours_left": 50, "still_to_pay": 10,
                                   "waiting_on": "the calendar" if number % 2 else "money", "name": "Project %d" % number}
         for number in range(40)}
lines = _state_running({"active": crowd})
check("a long run of active projects is bounded", len(lines) < 40, len(lines))
check("the rest are summarised by what they wait on and point at 'portfolio'",  # presentation: layout of the summary
      any("portfolio" in line and "calendar" in line and "money" in line for line in lines), lines[-3:])
few = _state_running({"active": dict(list(crowd.items())[:3])})
check("a short list is shown in full", sum(1 for line in few if line.startswith("  project_")) == 3, few)
