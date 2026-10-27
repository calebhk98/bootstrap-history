"""Regression coverage for Complaint 13: specialist venture supervision.

A concern whose crew mixes generic artisans with a skilled trade needs a foreman of that trade, one specialist
oversees a bounded number of concerns, and the open gate refuses without one. The rules are called on a stub game
(`venture_foreman_free`, `OpenGateMixin.staffing_open_refusal`; who is the foreman is `business_crew_rule.foreman`, tested in
test_business_crew_rule) and the screen on a built
reply; the ventures row's specialist field is test_craftsmen_wording_rules."""
QUICK_TOPIC = True

import types
from sim.tests import workforce_stand_in

from .harness import *
from sim.agents import business_crew_rule
from sim.engine.projects_open_gate import OpenGateMixin
from sim.engine.projects_ventures import VenturesMixin
from sim.refusal import cause_of, facts_of
from sim.ui.proto.render import render_pretty

SHARE = VenturesMixin.VENTURE_FOREMAN_SHARE


def a_game(nodes, employees=None, operating=(), capabilities=()):
    household = types.SimpleNamespace(employees=dict(employees or {}))
    game = types.SimpleNamespace(
        nodes=nodes, CAPABILITY_INSTITUTIONS=set(capabilities), VENTURE_FOREMAN_SHARE=SHARE,
        workforce=household, view=workforce_stand_in.view_of(household), state=types.SimpleNamespace(household=household, projects=types.SimpleNamespace(operating=set(operating))),
        institution_units=lambda node_id: 1.0, venture_garrison=lambda node_id, units: {},
        venture_staff_free=lambda: (99.0, 99.0), venture_hands=lambda node_id: (0.0, 0.0))
    game.venture_foreman = lambda node_id: business_crew_rule.foreman(business_crew_rule.figures_of(
        nodes[node_id], lambda: "labourer", 2000.0, 0.5, lambda: 300.0, SHARE, node_id in game.CAPABILITY_INSTITUTIONS, {}))
    game.venture_foremen_used = lambda excluding=None: VenturesMixin.venture_foremen_used(game, excluding)
    game.venture_foreman_free = lambda trade, excluding=None: VenturesMixin.venture_foreman_free(game, trade, excluding)
    return game


MIRROR = {"rev": 50.0, "lab": {"artisan": 400.0, "glassblower": 300.0, "smith": 100.0}}
GENERIC = {"rev": 50.0, "lab": {"artisan": 400.0, "labourer": 200.0}}

# --- who a concern needs as its foreman is `business_crew_rule.foreman` (test_business_crew_rule holds the cases: the largest
# skilled trade of a plant built with artisans; none for a generic plant, a plant with no takings or a capability institution).
game = a_game({"mirror": MIRROR, "generic": GENERIC})
check("a mirror concern needs a glassblower for a quarter of his year, and a generic one needs no specialist",
      game.venture_foreman("mirror") == ("glassblower", SHARE) and SHARE == 0.25 and game.venture_foreman("generic") == (None, 0.0),
      (game.venture_foreman("mirror"), game.venture_foreman("generic")))

# --- a specialist's free time -----------------------------------------------------------------------------------------
sites = {"mirror_%d" % number: MIRROR for number in range(5)}
busy = a_game({**sites, "new": MIRROR}, employees={"glassblower": 1}, operating=["mirror_%d" % number for number in range(3)])
check("a specialist's time is held by the concerns he is foreman of",
      busy.venture_foremen_used() == {"glassblower": 3 * SHARE} and abs(busy.venture_foreman_free("glassblower") - SHARE) < 1e-12,
      busy.venture_foremen_used())
check("a concern's own hold is left out when asking whether it can stay open",
      abs(busy.venture_foreman_free("glassblower", excluding="mirror_0") - 2 * SHARE) < 1e-12, "excluded hold counted")
check("one specialist has a bounded span of control: four quarter-FTE concerns, not an unlimited portfolio",
      a_game(sites, employees={"glassblower": 1}, operating=list(sites)[:4]).venture_foreman_free("glassblower") == 0.0
      and busy.venture_foreman_free("glassblower") > 0.0, "span of control unbounded")

# --- the open gate --------------------------------------------------------------------------------------------------------
def gate(game, node_id="new"):
    return OpenGateMixin.staffing_open_refusal(game, node_id)


why = gate(a_game({"new": MIRROR}))
check("generic artisans alone cannot supervise an advanced mirror concern",
      cause_of(why) == "foreman_missing" and facts_of(why)["trade"] == "glassblower", why)
why = gate(a_game({"new": MIRROR}, employees={"smith": 1}))
check("an unrelated specialist cannot supervise plate-mirror work",
      cause_of(why) == "foreman_missing" and facts_of(why)["trade"] == "glassblower", why)
check("a glassblower foreman can supervise plate-mirror work",
      gate(a_game({"new": MIRROR}, employees={"glassblower": 1})) is None, "refused with a glassblower")
check("a specialist already supervising four concerns cannot take a fifth",
      cause_of(gate(a_game({**sites, "new": MIRROR}, employees={"glassblower": 1}, operating=list(sites)[:4]))) == "foreman_missing", "fifth taken")

# --- the screen --------------------------------------------------------------------------------------------------------
screen = render_pretty("ventures", {"ok": True, "running": [
    {"id": "mirror_amalgam", "earns_a_year": 900.0, "costs_a_year": 400.0, "needs": {"scholars": 0, "craftsmen": 1},
     "specialist_foreman": {"trade": "glassblower", "fte": 0.25}}]})
check("the rendered ventures screen names the specialist foreman",  # presentation: the ventures screen's wording
      "specialist foreman: 0.25 glassblower FTE" in screen, screen)
