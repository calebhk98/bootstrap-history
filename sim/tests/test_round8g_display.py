"""round8g_display: a five-report playtest sweep of the display. The rules run on built inputs, with no game:
the repeated window of a hazard on `risk`, the money warnings of a `path`, the substitution gate, the society's
`needs_first` gates, and the data findings of the sweep (the tree's req_any, notes, risks, and which institutions are
capabilities). The commands over a stand-in are test_capability_and_train_handlers."""
import copy
import re
from types import SimpleNamespace

from .harness import check, NODES, S

from sim.tests.diffusion_host import gated
from sim.tests import projects_host
from sim.ui.protocol import render_risk as _render_risk
from sim.ui.proto.dispatch_inspection_path import route_money_warnings

QUICK_TOPIC = True

# --- `risk`: a per-year chance is rolled every year of its window, and the screen says what the window adds up to
def _risk_reply(year, hazard_years, per_year, after=None):
    hazard = {"name": "A sacking", "years": hazard_years, "sacks_a_site": True, "sack_chance_per_year": per_year}
    if after is not None:
        hazard["sack_chance_after_what_you_have_built"] = after
    return {"year": year, "knowledge_risk": {"technologies_at_risk": 5, "known_hazards_ahead": [hazard]}}


def _window_line(reply):
    return next(line for line in _render_risk(reply).splitlines() if "checked EVERY year" in line)


# presentation: the risk screen says a per-year hazard is checked every year of its window and what that adds up to
check("risk says a per-year hazard is rolled EVERY year of its window, with the years it spans",
      "10-year window" in _window_line(_risk_reply(240, [240, 249], 0.1)), _window_line(_risk_reply(240, [240, 249], 0.1)))
# presentation: the cumulative figure printed beside the per-year one
check("...and the chance across the window is 1 - (1 - p)^years, higher than the bare per-year figure (10 years at 10% is 65%)",
      "65%" in _window_line(_risk_reply(240, [240, 249], 0.1)), _window_line(_risk_reply(240, [240, 249], 0.1)))
# presentation: a window already begun counts only the years that remain
check("a window already begun counts only the years left in it (from 245: 5 years at 10% is 41%)",
      "5-year window" in _window_line(_risk_reply(245, [240, 249], 0.1)) and "41%" in _window_line(_risk_reply(245, [240, 249], 0.1)))
# presentation: the figure uses the chance after what the founder has built
check("what the founder has built lowers the cumulative figure it prints (5% after defences over 10 years is 40%)",
      "40%" in _window_line(_risk_reply(240, [240, 249], 0.1, after=0.05)), _window_line(_risk_reply(240, [240, 249], 0.1, after=0.05)))
check("a hazard with no per-year sack chance prints no window line",
      "checked EVERY year" not in _render_risk(_risk_reply(240, [240, 249], 0)))

# --- `path`: the money warnings of the route's startable steps
def _words(amount):
    return "{:,.0f} coin".format(amount)


check("with nothing startable on the route there is no warning", route_money_warnings(0, False, 0.0, 100.0, _words) == {})
check("a route with a step that pays its way gets no 'pays for nothing' warning, whoever is poor",
      route_money_warnings(3, True, 5000.0, 100.0, _words) == {})
knowledge = route_money_warnings(3, False, 50.0, 100.0, _words)
check("a route none of whose startable steps pays its way is told so, from turn one, and where to find what does pay",
      set(knowledge) == {"this_route_pays_for_nothing"} and "3 things" in knowledge["this_route_pays_for_nothing"]
      and '"sort":"earns"' in knowledge["this_route_pays_for_nothing"], knowledge)
combined = route_money_warnings(3, False, 5000.0, 1234.0, _words)
check("...and when the bill of the listed steps together passes what can be raised, it names both sums",
      "5,000 coin" in combined["these_together_cost_more_than_you_can_raise"]
      and "1,234 coin" in combined["these_together_cost_more_than_you_can_raise"], combined)
check("a combined bill exactly what can be raised is not over it",
      "these_together_cost_more_than_you_can_raise" not in route_money_warnings(3, False, 100.0, 100.0, _words))


# --- the substitution gate: the best option of each group, multiplied; none in a group means none at all
def _gate(nodes, bests):
    """The projects module over a tree, with the best option of each `req_any` group given."""
    module = projects_host.build(tree=nodes)
    module._group_best = lambda node_id, group, done: bests[group["group"]]
    return module


_groups = {"engine": {"req_any": [{"group": "fuel"}, {"group": "vessel"}]}, "plain": {"req_any": []}}
check("a node with no req_any gate clears it trivially, at full quality",
      _gate(_groups, {})._substitution_quality("plain") == (1.0, True))
passing = _gate(_groups, {"fuel": 0.5, "vessel": 0.8})
check("each group's best option multiplies into the quality",
      passing._substitution_quality("engine") == (0.4, True) and passing.last_substitution_gap() is None)
dead = _gate(_groups, {"fuel": 0.5, "vessel": 0.0})
check("a group with no option at all fails the gate and records which group was short",
      dead._substitution_quality("engine") == (0.0, False) and dead.last_substitution_gap() == ("a vessel", []),
      dead.last_substitution_gap())

# --- what the society must have first: the Mexica's draught animals gate the animal-drawn vehicles, and no others
MEXICA = S.load_civ("mexica_1500")
GATED_VEHICLES = ("tr_hopper_wagon", "lnd_two_wheel_cart", "lnd_four_wheel_cart", "mil_artillery_carriage", "pwr_animal_treadmill")
gate_node = MEXICA["needs_first"]["draught animals"]["node"]


def _Society(civ, done=()):
    return gated(civ, done)


check("the wheeled and animal-powered vehicles are in the same needs_first group as the harnesses, not a separate list",
      all(node_id in MEXICA["needs_first"]["draught animals"]["ids"] for node_id in GATED_VEHICLES)
      and "horse_collar" in MEXICA["needs_first"]["draught animals"]["ids"])
mexica = _Society(MEXICA)
check("a Mexica founder who has not imported draught animals cannot start any of the vehicles",
      all(mexica.needs_first(node_id)[0] == gate_node for node_id in GATED_VEHICLES),
      [(node_id, mexica.needs_first(node_id)) for node_id in GATED_VEHICLES])
check("importing draught animals lifts the gate on all of them",
      all(_Society(MEXICA, done=(gate_node,)).needs_first(node_id)[0] is None for node_id in GATED_VEHICLES))
check("the wheel concept, human-powered wheeled transport and water-turned machinery are not swept into the gate",
      all(mexica.needs_first(node_id)[0] is None for node_id in ("lnd_wheel_spoked", "lnd_litter", "en_overshot_wheel")))
check("a society with no needs_first has no gate", _Society({}).needs_first("tr_hopper_wagon") == (None, None))

# --- which nodes are capability institutions is data (the `capability` mechanic), not a list in the display code
capabilities = {node_id for node_id, node in NODES.items() if "capability" in (node.get("mechanics") or {})}
check("workshop_first and identity_cover declare the capability mechanic, and an ordinary prerequisite does not",
      {"workshop_first", "identity_cover"} <= capabilities and "scientific_method" not in capabilities
      and "tex_horizontal_loom" not in capabilities)

# --- data findings of the sweep
check("point_contact_transistor no longer gates on single_crystal/silicon_path - the contradiction between its own "
      "note and its prerequisite graph is gone",
      NODES["point_contact_transistor"]["req_any"] == [], NODES["point_contact_transistor"]["req_any"])
check("...while single_crystal is still mandatory for the manufacturable junction transistor",
      "single_crystal" in NODES["junction_transistor"]["pre"], NODES["junction_transistor"]["pre"])


# THE BUG CLASS, not just the one instance: a node's own note disclaiming a prerequisite ("no X and no Y, neither of
# which existed yet", "X had not yet been invented", ...) while `pre` or a req_any option still names that same thing.
# The window searched is the disclaiming sentence itself, narrowed to the actual "no X"/"without X" spans in it.
def _disclaimed_prereq_contradictions(nodes):
    disclaim_pats = (r"neither of which existed yet", r"none of which existed yet",
                     r"did not yet exist", r"had not yet been invented",
                     r"not yet invented", r"yet to be invented")
    negation_span = re.compile(
        r"\b(?:no|without)\s+([a-z][a-z\- ]{2,40}?)"
        r"(?=\s*,|\s+and\s+no\b|\s+and\s+without\b|\s+neither\b|\s+none\b|\s*\.|$)")
    stop = set("and the for with from that this into over under being than "
               "then which what when were was has have had does did already "
               "both only also even more most make made gives give were "
               "being could would should before after still about".split())

    def keywords(text):
        return {word for word in re.findall(r"[a-z]{5,}", text.lower()) if word not in stop}

    out = []
    for node_id, node in sorted(nodes.items()):
        low = (node.get("note") or "").lower()
        hit = None
        for pattern in disclaim_pats:
            match = re.search(pattern, low)
            if match:
                hit = match
                break
        if not hit:
            continue
        sentence_start = low.rfind(".", 0, hit.start())
        sentence_start = 0 if sentence_start == -1 else sentence_start + 1
        window = low[sentence_start:hit.start()]
        window_keywords = set()
        for span in negation_span.findall(window):
            window_keywords |= keywords(span)
        if not window_keywords:
            continue
        prereq_ids = list(node.get("pre") or [])
        for req_group in (node.get("req_any") or []):
            prereq_ids.extend((req_group.get("options") or {}).keys())
        for prereq_id in prereq_ids:
            prereq_node = nodes.get(prereq_id)
            if not prereq_node:
                continue
            prereq_keywords = keywords(prereq_node.get("name") or "") | {prereq_id.lower()}
            if window_keywords & prereq_keywords:
                out.append((node_id, prereq_id, hit.group(0), sorted(window_keywords & prereq_keywords)))
    return out


check("the bug class: no node's note disclaims a prerequisite as not having existed yet while the node's own pre or "
      "req_any (including a genuine multi-option substitution) still requires it",
      _disclaimed_prereq_contradictions(NODES) == [], _disclaimed_prereq_contradictions(NODES))
_nodes_predisclaim = copy.deepcopy(NODES)
_nodes_predisclaim["point_contact_transistor"]["req_any"] = [
    {"group": "semiconductor", "options": {"silicon_path": 0.9, "single_crystal": 1.0}}]
check("...and the scanner is not vacuous: it does flag the original, now-fixed req_any when restored on a copy of the tree",
      _disclaimed_prereq_contradictions(_nodes_predisclaim) != [], _disclaimed_prereq_contradictions(_nodes_predisclaim))

# EVERY `located_material` node rolls its risk every year it is active, with no modifier: a near-certain failure is an
# unrevisited placeholder, not a researched figure.
_located_risks = {node_id: node["risk"] for node_id, node in NODES.items() if node.get("cat") == "located_material"}
check("no located_material node rolls a near-certain failure every year (0.95 was a placeholder copied across ten nodes)",
      _located_risks and max(_located_risks.values()) <= 0.3, sorted(_located_risks.items(), key=lambda kv: -kv[1])[:3])

# a data file is not something a player's own note should ever send them to read
_geo_leaks = [node_id for node_id, node in NODES.items() if "data/world/" in (node.get("note") or "")]
check("no node's player-facing note sends the player to read a data file out of the game",
      _geo_leaks == [], _geo_leaks)
