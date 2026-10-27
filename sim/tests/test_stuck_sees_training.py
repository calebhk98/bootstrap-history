"""Complaint 573: `stuck` reads the same work in hand as `state`, training included. Complaint 640: the readings are
called on a stand-in game that holds only its projects and its training; no game is played."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto.dispatch_inspection_stuck import _stuck_started_nothing, _stuck_training_in_hand
from sim.ui.proto.state_projects import training_in_hand
from sim.tests.ui_stand_in import Game

# rows are [capacity, ready_year] for people bought and trained, [0, ready_year, trade, count] for a trade being taught
TRAINING = [[1.5, 105], [0, 107, "machinist", 2]]
training_game = Game(active={}, view=lambda name: (lambda: TRAINING), project_cost=lambda node_id: 1.0)
idle_game = Game(active={}, view=lambda name: (lambda: []), project_cost=lambda node_id: 1.0)

check("with only training running stuck does not report an idle household",
      _stuck_started_nothing(training_game, ["a"], ["a"]) is None)
check("with nothing running stuck reports an idle household",
      (_stuck_started_nothing(idle_game, ["a"], ["a"]) or {}).get("kind") == "idle")
check("a project in hand is not idle either", _stuck_started_nothing(Game(active={"p": {}}, view=lambda name: (lambda: [])), [], []) is None)

rows = training_in_hand(training_game)
check("training rows read by index: people bought and trained, and a trade being taught",
      rows == [{"artisan_capacity": 1.5, "ready_year": 105, "trade": None, "people": None},
               {"artisan_capacity": 0, "ready_year": 107, "trade": "machinist", "people": 2}], rows)
reason = _stuck_training_in_hand(training_game)
check("stuck names the training state shows", reason["each_training"] == rows and reason["how_many"] == 2 and reason["kind"] == "active",
      reason)
check("stuck names no training when there is none", _stuck_training_in_hand(idle_game) is None)
