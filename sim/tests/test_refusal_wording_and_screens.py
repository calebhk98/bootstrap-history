"""Refusal wording and screens: the patronage refusal never leaks an id nor recommends a refusal, the policy screen
groups what is running from what is not, and "nothing else rests on this" means zero. The start rule is the real mixin
over a stand-in game (stage of the patron, interest and fog set by the test); the screens are rendered from built
replies (no game). The auto_open policy through a game is test_refusal_wording_and_screens_scenario."""
import collections
from types import SimpleNamespace

from .harness import check, NODES

from sim.engine.projects_starting import StartingMixin
from sim.engine.ui_port import downstream_count
from sim.ui import protocol as _PROTO
from sim.ui.proto.techtree import _explain_unlocks, _rests_band

QUICK_TOPIC = True


class _World(StartingMixin):
    """The social approval rule and the patron advice, over a patron, a state interest and a fog switch."""

    def __init__(self, interest=-0.8, fog=False, visible=("patron_local",), done=(), running=(),
                 protection=0.0, prereqs=(), opposed_patron=None):
        self.fog_on = fog
        self.interest = interest
        self.visible = set(visible)
        self.running_ids = set(running)
        self.nodes = {"patron_local": {"pre": list(prereqs)}, "patron_senatorial": {"pre": []},
                      "plain": {"cat": "technique"}}
        self.state = SimpleNamespace(projects=SimpleNamespace(done=set(done)),
                                     household=SimpleNamespace(protection=protection))
        self.opposed_patron = opposed_patron

    def state_interest(self, node):
        return self.interest

    def approval_patron(self, gate):
        return "patron_local" if gate == "wary" else self.opposed_patron

    def running(self, node_id):
        return node_id in self.running_ids

    def is_visible(self, node_id):
        return not self.fog_on or node_id in self.visible


def _refusal(world, category="technique"):
    return world._check_social_approval("plain", {"cat": category}, False, {}, True)


# --- the patronage refusal under fog: no id for a node the founder has never heard of
fogged = _World(fog=True, visible=())
allowed, wary = _refusal(fogged)
check("the patronage refusal fires for a wary state at all, so the rest of these checks test something real",
      allowed is False and wary, wary)
check("...and does not name patron_local, which this founder has never heard of and could not start",
      "patron_local" not in wary, wary)
# presentation: the advice stays useful in words once the id is withheld
check("...and still says what is wanted, in words rather than an id",
      "patron" in wary and "before anyone here will let you begin" in wary, wary)

# --- a refusal may never recommend a refusal: name the command only when it would be accepted
blocked_patron = _World(fog=False, visible=("patron_local",), prereqs=("identity_cover",))
_allowed, advice = _refusal(blocked_patron)
check("without fog, a patron that itself lacks a prerequisite is not recommended by command: the refusal says what it wants",
      "start patron_local" not in advice and "identity_cover" in advice, advice)
fog_missing = _World(fog=True, visible=("patron_local",), prereqs=("identity_cover",))
_allowed, advice = _refusal(fog_missing)
check("...and a missing prerequisite the founder has not heard of is not named either",
      "identity_cover" not in advice and "something you have not heard of" in advice, advice)
startable = _World(fog=False, visible=("patron_local",), prereqs=())
_allowed, advice = _refusal(startable)
check("once patron_local IS startable, the refusal hands over the exact command",
      "start patron_local" in advice, advice)
built = _World(fog=False, done=("patron_local",))
_allowed, advice = _refusal(built)
check("a patron already built but not open is to be opened, not started", "open patron_local" in advice, advice)

# --- the gate itself
check("a state that is not wary lets the work begin", _refusal(_World(interest=0.5)) is None)
check("a wary state with the patron's concern running lets the work begin",
      _refusal(_World(running=("patron_local",))) is None)
check("the patronage, institution and material categories are never asked for permission",
      all(_refusal(_World(), category) == (True, None) for category in ("social", "institution", "foundation", "capability", "material")))
opposed = _World(interest=-2.0, opposed_patron="patron_senatorial", fog=True, visible=(), running=("patron_local",))
_allowed, text = _refusal(opposed)
check("a state that actively opposes the work refuses it, and does not leak the senatorial patron's id under fog",
      _allowed is False and "patron_senatorial" not in text and "protection" in text, text)
opposed.state.household.protection = 100.0
check("enough protection overrides an opposing state", _refusal(opposed) is None)

# --- the policy screen groups by what is actually running
reply = {"policy": {"auto_open": False, "auto_hire": True, "reserve_staff": False, "auto_replace_foreman": True},
         "what_each_does": {name: "does %s" % name for name in ("auto_open", "auto_hire", "reserve_staff", "auto_replace_foreman")}}
screen = _PROTO.render_policy(reply)
# presentation: the policy screen heads the running and not-running switches
check("the policy screen says which automatic behaviours are running now and which are only descriptions",
      "RUNNING NOW:" in screen and "NOT RUNNING" in screen and "WOULD do if you turned it on" in screen, screen[:300])
running_part, not_running_part = screen.split("NOT RUNNING")
check("...with the running switches in the first group and the others in the second, each listed exactly once",
      all(name in running_part for name in ("auto_hire", "auto_replace_foreman"))
      and all(name in not_running_part for name in ("auto_open", "reserve_staff"))
      and all(screen.count("  %-18s " % name) == 1 for name in reply["policy"]), screen)
nothing = _PROTO.render_policy({"policy": {"auto_open": False}, "what_each_does": {}})
# presentation: the policy screen says plainly that nothing is automatic
check("with every switch off the screen says nothing is automatic", "nothing is automatic" in nothing, nothing)

# --- "nothing else rests on this" has to mean zero
check("only a genuine zero is described as having nothing resting on it",
      _rests_band(0).startswith("nothing else")
      and not any(_rests_band(count).startswith("nothing else") for count in (1, 2, 3, 4, 41, 301, 1201)),
      [(count, _rests_band(count)) for count in (0, 1, 2, 3, 4)])
check("...and the bands still climb, so the new rung did not break the ladder",
      len({_rests_band(count) for count in (0, 1, 4, 41, 301, 1201)}) == 6)
check("...and every band has a short form for the column that renders it",
      all(_rests_band(count) in _PROTO._RESTS_SHORT for count in (0, 1, 4, 41, 301, 1201)), sorted(_PROTO._RESTS_SHORT))

# the two pairs a player reported, through the part of `why` that states it (under fog, where it is banded)
fog_game = SimpleNamespace(fog=True, goal="nowhere")
for prerequisite, dependent in (("met_ore_crushing_sorting", "met_jigging_gravity"),
                                ("in2_tape_measure_steel", "in2_baseline_measurement_apparatus")):
    dependents = downstream_count(NODES, prerequisite)
    rests = _explain_unlocks(fog_game, NODES, prerequisite, [], dependents)["how_much_rests_on_this"]
    check("%s does not claim nothing rests on it, when %s names it as a missing prerequisite" % (prerequisite, dependent),
          prerequisite in NODES[dependent]["pre"] and dependents >= 1 and not rests.startswith("nothing else"),
          (rests, NODES[dependent]["pre"]))
check("off fog `why` gives the exact count and no band",
      _explain_unlocks(SimpleNamespace(fog=False, goal="nowhere"), NODES, "met_ore_crushing_sorting", [], 7)["downstream_count"] == 7
      and _explain_unlocks(SimpleNamespace(fog=False, goal="nowhere"), NODES, "met_ore_crushing_sorting", [], 7)["how_much_rests_on_this"] is None)

# and the class: no node with a dependent may say nothing rests on it
dependents_of = collections.Counter()
for node in NODES.values():
    for prerequisite in node["pre"]:
        dependents_of[prerequisite] += 1
liars = [node_id for node_id in sorted(NODES)
         if dependents_of[node_id] > 0 and _rests_band(dependents_of[node_id]).startswith("nothing else")]
check("no node in the whole tree that something else depends on is described as having nothing resting on it",
      not liars, liars[:8])
