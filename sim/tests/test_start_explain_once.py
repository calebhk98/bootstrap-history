"""Complaint 76: a long explanation is shown once per game, then a pointer; a command's `full` flag shows it again. The
rule (`already_explained`) is called on a stub game holding a seat's progress record."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.state_holdings import SeatProgressState
from sim.ui.proto.explain_once import already_explained
from sim.tests.ui_stand_in import Game


def stub_game(year=100):
    return Game(state=Game(acting_record=Game(seat_progress=SeatProgressState())), year=year)


game = stub_game()
check("the first time a topic is shown it is not yet explained", already_explained(game, "start_price_fixed", {}) is False)
check("the second time it is", already_explained(game, "start_price_fixed", {}) is True)
check("`full` shows it again, and the record is not forgotten", already_explained(game, "start_price_fixed", {"full": True}) is False
      and already_explained(game, "start_price_fixed", {}) is True)
check("another topic is explained on its own", already_explained(game, "start_untrained_trade", {}) is False)
check("`full` on a topic never shown still marks it shown",
      already_explained(game, "third", {"full": True}) is False and already_explained(game, "third", {}) is True)
check("the record keeps the year each topic was first shown",
      game.state.acting_record.seat_progress._said_explanations == {"start_price_fixed": 100, "start_untrained_trade": 100, "third": 100},
      game.state.acting_record.seat_progress._said_explanations)
later = stub_game(year=130)
later.state.acting_record.seat_progress._said_explanations = {"start_price_fixed": 100}
already_explained(later, "other", {})
check("a topic first shown later is dated then, and the old one keeps its year",
      later.state.acting_record.seat_progress._said_explanations == {"start_price_fixed": 100, "other": 130}, later.state.acting_record.seat_progress._said_explanations)
