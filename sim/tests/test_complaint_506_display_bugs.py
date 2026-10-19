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

# --- market <material> ---------------------------------------------------------------------------------------
from sim.ui.market_report import priceable_materials

_priced = priceable_materials(_game)
_one = _priced[0]
check("'market <material>' parses the material", _parse_typed("market %s" % _one)[0] == {"cmd": "market", "material": _one},
      _parse_typed("market %s" % _one))
check("'market offset 5' is still paging", _parse_typed("market offset 5")[0] == {"cmd": "market", "offset": 5},
      _parse_typed("market offset 5"))
_filtered = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": _one})
check("'market <material>' lists that one material only",
      _filtered.get("ok") and [row["material"] for row in _filtered["materials"]["rows"]] == [_one], _filtered)
check("...and the wages table is left out", _filtered["wages"] == [] and "WAGES" not in _render_pretty("market", _filtered),
      _render_pretty("market", _filtered))
_unknown = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": "zzzz_nothing"})
check("an unknown material is refused and points back to the full table",
      _unknown.get("ok") is False and "'market' lists them all" in _unknown["error"], _unknown)
_typo = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": _one[:-1] + "x"})
check("a near miss suggests the real name", _typo.get("ok") is False and _one in _typo["error"], _typo)

# --- quote sell concern ---------------------------------------------------------------------------------------
import copy as _copy
import random as _random
from sim.agents.api import ActorRecord


def _sale_game():
    template = next(node_id for node_id, node in NODES.items() if not node["pre"] and node["cap"] >= 0)
    node = _copy.deepcopy(NODES[template])
    node.update(id="zz_quoted", name="zz_quoted", traits=["commerce"], pre=[], lab={"labourer": 100.0}, mat={},
                rev=5000.0, up=100.0, yrs=1.0, risk=0.0, ph=0.0, dev_years=None, dev_people=None, cap=0.0, art=0.2, sch=0.0)
    node.pop("gains", None)
    nodes = _copy.deepcopy(NODES)
    nodes["zz_quoted"] = node
    game = build_unopened(lambda: S.Sim(nodes, list(ORDER), _random.Random(1), events=False, manual=True,
                                        civ=S.load_civ("rome_100ad")))
    game.goal, game.done_year = GOAL, {}
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add("zz_quoted")
    projects.done_year["zz_quoted"] = year - 5
    projects.operating.add("zz_quoted")
    projects.business.set_opened_year("zz_quoted", year - 5)
    game._done_changed()
    game.actors.add("firm:rich", ActorRecord(kind="firm", money=1.0e9, knowledge={"zz_quoted"}))
    return game, nodes


_sale, _sale_nodes = _sale_game()
check("'quote sell concern <id>' parses", _parse_typed("quote sell concern zz_quoted")[0]
      == {"cmd": "quote", "what": "sell", "target": "concern", "id": "zz_quoted"}, _parse_typed("quote sell concern zz_quoted"))
_capital_before = _sale.household.capital
_preview = S._agent_dispatch(_sale, _sale_nodes, {"cmd": "quote", "what": "sell", "target": "concern", "id": "zz_quoted"})
check("the quote names the buyer and a price", _preview.get("ok") and _preview["buyer"] == "firm:rich" and _preview["price"] > 0,
      _preview)
check("a quote sells nothing", "zz_quoted" in _sale.state.projects.operating and _sale.household.capital == _capital_before)
_actual = S._agent_dispatch(_sale, _sale_nodes, {"cmd": "sell", "what": "concern", "id": "zz_quoted"})
check("the sale settles at exactly the quoted buyer and price",
      _actual.get("ok") and _actual["price"] == _preview["price"] and _actual["buyer"] == _preview["buyer"], (_preview, _actual))
_gone = S._agent_dispatch(_sale, _sale_nodes, {"cmd": "quote", "what": "sell", "target": "concern", "id": "zz_quoted"})
check("a concern no longer run cannot be quoted", _gone.get("ok") is False, _gone)

# --- why <material> and the shortage line ---------------------------------------------------------------------
from sim.engine.shortage_conditions import material_words, slowed_projects

check("a material key reads in player words", material_words("alum_kg") == "alum" and material_words("hectare_land") == "hectare land",
      (material_words("alum_kg"), material_words("hectare_land")))
_materials_with_price = [key for key in _priced if key.endswith("_kg")]
_why_material = S._agent_dispatch(_game, NODES, {"cmd": "why", "id": _materials_with_price[0]})
check("'why <material>' explains the material instead of calling it an unknown node",
      _why_material.get("ok") and _why_material.get("material_story") == _materials_with_price[0], _why_material)
check("...and reads as text naming the material in words",
      material_words(_materials_with_price[0]) in _render_pretty("why", _why_material),
      _render_pretty("why", _why_material))
_nothing = S._agent_dispatch(_game, NODES, {"cmd": "why", "id": "zzzz_nothing"})
check("'why' on a name that is neither still says it is unknown", _nothing.get("ok") is False and "unknown" in _nothing["error"], _nothing)
check("with no project running nothing is slowed by a shortage", slowed_projects(_game) == [], slowed_projects(_game))

_shortage_game = unopened_sim()
_shortage_game.resource_throttle = lambda: 0.2
_shortage_game.state.holdings.binding = "alum_kg"
_shortage_game.state.household.log.clear()
_shortage_game._step_materials()
check("no 'SHORT OF' line is logged when no running project draws the short material",
      not any("SHORT OF" in str(entry[1]) for entry in _shortage_game.state.household.log),
      [entry for entry in _shortage_game.state.household.log if "SHORT OF" in str(entry[1])])
