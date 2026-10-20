"""Complaint 640, audit batch 3, scenario: the commands behind the small display fixes of complaint 506 answer from a
game. The functions behind them have tests of their own: test_complaint_506_display_bugs."""
import copy as _copy
import random as _random

from .harness import *  # noqa: F401,F403
from sim.agents.api import ActorRecord
from sim.engine.shortage_conditions import material_words
from sim.ui.market_report import priceable_materials
from sim.ui.proto.render_typed import render_pretty as _render_pretty

_game = unopened_sim()
_bare_path = S._agent_dispatch(_game, NODES, {"cmd": "path"})
check("scenario display: a bare `path` replies with the goal's route", _bare_path.get("ok") and _bare_path.get("id") == GOAL,
      _bare_path.get("error"))

# ---- market <material> ----
_priced = priceable_materials(_game)
_one = _priced[0]
_filtered = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": _one})
check("scenario display: 'market <material>' lists that one material and leaves the wages out",
      _filtered.get("ok") and [row["material"] for row in _filtered["materials"]["rows"]] == [_one]
      and _filtered["wages"] == [], _filtered)
_unknown = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": "zzzz_nothing"})
_typo = S._agent_dispatch(_game, NODES, {"cmd": "market", "material": _one[:-1] + "x"})
check("scenario display: an unknown material is refused, and a near miss suggests the real name",
      _unknown.get("ok") is False and _typo.get("ok") is False and _one in _typo["error"], (_unknown, _typo))

# ---- why <material> ----
_materials_with_price = [key for key in _priced if key.endswith("_kg")]
_why_material = S._agent_dispatch(_game, NODES, {"cmd": "why", "id": _materials_with_price[0]})
check("scenario display: 'why <material>' explains the material, in words, instead of calling it an unknown node",
      _why_material.get("ok") and _why_material.get("material_story") == _materials_with_price[0]
      and material_words(_materials_with_price[0]) in _render_pretty("why", _why_material), _why_material)
_nothing = S._agent_dispatch(_game, NODES, {"cmd": "why", "id": "zzzz_nothing"})
check("scenario display: 'why' on a name that is neither still says it is unknown",
      _nothing.get("ok") is False and "unknown" in _nothing["error"], _nothing)

# ---- a shortage no running project draws is not logged ----
_shortage_game = unopened_sim()
_shortage_game.resource_throttle = lambda: 0.2
_shortage_game.state.holdings.binding = "alum_kg"
_shortage_game.state.household.log.clear()
_shortage_game._step_materials()
check("scenario display: no 'SHORT OF' line is logged when no running project draws the short material",
      not any("SHORT OF" in str(entry[1]) for entry in _shortage_game.state.household.log),
      [entry for entry in _shortage_game.state.household.log if "SHORT OF" in str(entry[1])])


# ---- quote sell concern ----
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
_capital_before = _sale.household.capital
_quote = {"cmd": "quote", "what": "sell", "target": "concern", "id": "zz_quoted"}
_preview = S._agent_dispatch(_sale, _sale_nodes, _quote)
check("scenario display: the quote of a concern's sale names the buyer and a price and sells nothing",
      _preview.get("ok") and _preview["buyer"] == "firm:rich" and _preview["price"] > 0
      and "zz_quoted" in _sale.state.projects.operating and _sale.household.capital == _capital_before, _preview)
_actual = S._agent_dispatch(_sale, _sale_nodes, {"cmd": "sell", "what": "concern", "id": "zz_quoted"})
check("scenario display: the sale settles at exactly the quoted buyer and price",
      _actual.get("ok") and _actual["price"] == _preview["price"] and _actual["buyer"] == _preview["buyer"], (_preview, _actual))
check("scenario display: a concern no longer run cannot be quoted",
      S._agent_dispatch(_sale, _sale_nodes, _quote).get("ok") is False)
