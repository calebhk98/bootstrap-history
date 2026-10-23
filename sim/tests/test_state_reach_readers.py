"""Complaint 658: what a state enforces, lends against, notices and answers follows its reach, the share its paid officials
collect over its roads (620), not a typed capacity. Each reader is called with a reach the test sets and moves the way its rule
says; the home world's reach under unpaid officials is in test_collection_view_staff and test_staff_reach_wiring."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.agents import enforcement
from sim.agents.api import Government
from sim.agents.records import ActorRecord
from sim.engine.data import load_civ
from sim.engine.diffusion_rules import medical_relief
from sim.engine.legitimacy import LegitimacyMixin
from sim.engine.society_state_pressure import StatePressureMixin
from .agents_fake_world import FakeWorld

QUICK_TOPIC = True

FULL_REACH, LOW_REACH = 0.9, 0.3


class ReachWorld(FakeWorld):
    """A world whose state reaches as far as the test says, with one patent held by someone else."""

    def __init__(self, reach):
        super().__init__()
        self.reach = reach

    def state_reach(self):
        return self.reach

    def patent_entry(self, node_id):
        return {"holder": "holder", "licensees": []}


check("no civilisation record carries a typed state capacity",
      all("state_capacity" not in load_civ(civ_id)
          for civ_id in ("rome_100ad", "norse_900ad", "han_china_100ad", "england_1300", "mexica_1500")))

# ---- the readers --------------------------------------------------------------------------------------------
state = Government("government:home", ActorRecord(kind="government", money=0.0))
check("lenders trust a state as far as it reaches",
      state.credit_standing(ReachWorld(LOW_REACH)) < state.credit_standing(ReachWorld(FULL_REACH))
      and state.credit_standing(ReachWorld(FULL_REACH)) == FULL_REACH)
check("a patent is enforced less often where the state reaches less",
      enforcement.expected_damages(ReachWorld(LOW_REACH), "infringer", "node", 100.0)
      < enforcement.expected_damages(ReachWorld(FULL_REACH), "infringer", "node", 100.0))
check("the state's expected damages are its reach times the margin made",
      abs(enforcement.expected_damages(ReachWorld(LOW_REACH), "infringer", "node", 100.0) - LOW_REACH * 100.0) < 1e-9)
check("public-health guidance is followed less where the state reaches less",
      medical_relief(1.0, 0.5, LOW_REACH) < medical_relief(1.0, 0.5, FULL_REACH))


def notice(reach, scale):
    """The home state's notice of a household of this scale, from the real method over a stand-in game."""
    return StatePressureMixin.state_notice(SimpleNamespace(state_reach=lambda: reach, household_scale=lambda: scale))


check("a state that reaches less notices a household less", notice(LOW_REACH, 0.5) < notice(FULL_REACH, 0.5))
check("the same reach notices a larger household more", notice(FULL_REACH, 0.2) < notice(FULL_REACH, 0.8))


def authority(reach, consent):
    return LegitimacyMixin.state_authority(SimpleNamespace(state_reach=lambda: reach, state_legitimacy=lambda: consent))


check("authority is the reach worn by consent", authority(0.8, 0.5) == 0.4 and authority(0.4, 0.5) < authority(0.8, 0.5))

# ---- (b) needs specific staff: mines, order and woods are in test_state_guards_and_inspectors.py
