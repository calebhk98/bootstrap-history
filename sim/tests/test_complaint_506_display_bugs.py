"""Complaint 506: small display and wording bugs found in a Rome playtest."""
from .harness import *  # noqa: F401,F403
from sim.agents.group import InterestGroup
from sim.agents.group_strata import definite
from sim.engine.blockers import BLOCKER_MEANING
from sim.ui.cli_interactive import _civ_title
from sim.ui.proto.help import example_node_id
from sim.ui.proto.render_screen_why import _material_row_text
from sim.ui.proto.render_typed import render_pretty as _render_pretty
from sim.ui.proto.typed import parse_typed as _parse_typed
from sim.ui.proto.ventures import _VENTURE_SUPERVISION_NOTE

check("a petition says the blame lands on the founder when his share is material",
      "The blame lands on you" in InterestGroup.blame_words(1.0), InterestGroup.blame_words(1.0))
check("...and says nothing of blame when his share is slight", InterestGroup.blame_words(0.05) == "",
      InterestGroup.blame_words(0.05))

check("a stratum name that opens with an article is not given a second one",
      definite("The Roman Empire under Trajan artisans") == "the Roman Empire under Trajan artisans",
      definite("The Roman Empire under Trajan artisans"))
check("a proper name keeps its own opening and a common noun gets one",
      definite("Rome artisans") == "Rome artisans" and definite("artisans") == "the artisans",
      (definite("Rome artisans"), definite("artisans")))

_game = unopened_sim()
_levers = S._agent_dispatch(_game, NODES, {"cmd": "leverage"})
_levers_text = _render_pretty("leverage", _levers)
check("leverage reads as text, not Python dictionaries",
      "{" not in _levers_text and "literacy general" in _levers_text, _levers_text)

_quit = S._agent_dispatch(_game, NODES, {"cmd": "quit"})
check("quit prints a farewell, not the protocol field",
      "bye: True" not in _render_pretty("quit", _quit), _render_pretty("quit", _quit))

_example = example_node_id()
check("the usage example names a real node", _example in NODES, _example)
check("a bare path asks for the route to the goal", _parse_typed("path")[0] == {"cmd": "path"}, _parse_typed("path"))
_bare_path = S._agent_dispatch(_game, NODES, {"cmd": "path"})
check("...and the reply is the goal's route", _bare_path.get("ok") and _bare_path.get("id") == GOAL,
      _bare_path.get("error"))

_land = _material_row_text({"material": "hectare_land", "needed_tonnes": 0.008, "held_tonnes": 0.0,
                            "missing_tonnes": 0.008, "cost_of_missing": 10.0, "not_produced": True,
                            "own_unit": {"dimension": "area", "unit": "hectares", "needed": 8.0, "held": 0.0,
                                         "missing": 8.0}})
check("a land row is counted in hectares and not said to be supplied in years",
      "hectares" in _land and "lib" not in _land and "about" not in _land and "nothing produces" in _land, _land)

check("a BC start year is not repeated as a negative number",
      _civ_title({"name": "Ptolemaic Egypt, 100 BC", "year": -100}) == "Ptolemaic Egypt, 100 BC"
      and _civ_title({"name": "Somewhere", "year": -100}) == "Somewhere, 100 BC"
      and _civ_title({"name": "Rome", "year": 100}) == "Rome, 100 AD",
      (_civ_title({"name": "Somewhere", "year": -100}), _civ_title({"name": "Rome", "year": 100})))

check("the supervision note does not claim 0.13 is a third of a third",
      "third of a third" not in _VENTURE_SUPERVISION_NOTE, _VENTURE_SUPERVISION_NOTE)
check("the money blocker covers the yearly draw rate as well as the bill", "draw rate" in BLOCKER_MEANING["money"],
      BLOCKER_MEANING["money"])
