"""Complaint 99: `idle` sizes what the hours could do (people to teach, a development program). Complaint 640:
rules on a stub game built here; the whole-game replies are in test_idle_sized_suggestions_scenario."""
QUICK_TOPIC = True

import types

from .harness import *  # noqa: F401,F403
from sim.ui.proto.guidance import development_program, training_suggestions

_game = types.SimpleNamespace(HOURS_PER_PERSON_YEAR=2000.0, labour=types.SimpleNamespace(TEACHING_HOURS_PER_PERSON=300.0),
                              project_cost=lambda node_id: {"dear": 900.0, "cheap": 40.0, "also_cheap": 40.0}[node_id])

_rows = training_suggestions(_game, [
    {"trade": "machinist", "oversubscribed": True, "demand_hours_this_year": 5000.0, "supply_hours_this_year": 1000.0},
    {"trade": "smith", "oversubscribed": False, "demand_hours_this_year": 500.0, "supply_hours_this_year": 1000.0},
    {"trade": "mason", "oversubscribed": True, "demand_hours_this_year": 1001.0, "supply_hours_this_year": 1000.0}])
check("only oversubscribed trades get a teaching suggestion", [row["trade"] for row in _rows] == ["machinist", "mason"], _rows)
check("the people short are the shortfall in hours over a person's year, rounded up", _rows[0]["people_short"] == 2, _rows[0])
check("a shortfall of a single hour still asks for one person", _rows[1]["people_short"] == 1, _rows[1])
check("the teaching hours are the people times the hours teaching one takes", _rows[0]["teaching_hours"] == 600.0, _rows[0])
# presentation: the suggested command is the line a player types
check("the command is the train command for that trade and number", _rows[0]["command"] == "train machinist 2", _rows[0])
check("no oversubscribed trade, no suggestion", training_suggestions(_game, []) == [])

_nodes = {"dear": {"name": "Dear", "yrs": 4, "lab": {"smith": 800.0, "mason": 400.0}},
          "cheap": {"name": "Cheap", "yrs": 0, "lab": {"smith": 90.0}},
          "also_cheap": {"name": "Also", "yrs": 2, "lab": {}}}
_program = development_program(_game, _nodes, ["dear", "cheap", "also_cheap"])
check("the program is the startable project that costs least cash, ties by id", _program["id"] == "also_cheap", _program)
check("its cash cost is the project's cost", _program["cash_cost"] == 40.0, _program)
_dear = development_program(_game, _nodes, ["dear"])
check("its directed hours a year are its labour hours spread over its years", _dear["directed_hours_per_year"] == 300.0 and _dear["years"] == 4.0, _dear)
check("a project with no years is spread over one", development_program(_game, _nodes, ["cheap"])["directed_hours_per_year"] == 90.0)
check("with nothing startable there is no program", development_program(_game, _nodes, []) is None)
