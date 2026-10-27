"""Complaints 81, 83 and 127: what a finished or failed project logs, by kind and facts. The projects module's `_complete`, `failure_severity`,
`opening_shortfall` and `goal_effect_lines` run over plain values carrying only what they read; the severity, shortfall and goal
movement rules are test_completion_messaging."""

QUICK_TOPIC = True

from collections import Counter
from types import SimpleNamespace

from .harness import check

from sim.tests import projects_host
from sim.diffusion.api import ApplyTechEffects
from sim.knowledge.api import KnowledgeSeat, LearnTechnique, RevealFrom
from sim.production.api import RefreshDoneCaches
from sim.seats.api import RecordGoalReached
from sim.workforce.api import GrantStaff
from sim.knowledge.module import Knowledge
from sim.polity.api import AddGovernance, AddScandal, CarryOutTransfers, GainReputation
from sim.refusal import cause_of
from sim.tests import event_stand_in, module_harness, polity_host

NODE = "school"


def kinds(game):
    return [cause_of(line) for _year, line in game.state.household.log]


class Finishing:
    """A stand-in game with one active project, `school`, whose attempt is about to end."""

    def __init__(self, fails=False, venture=True, auto_open=False, shortfall=None, goal_lines=(), snapshot=None, hire_mode=False):
        household = SimpleNamespace(log=[], hour_allocations={"school": 1.0})
        self.state = SimpleNamespace(
            projects=SimpleNamespace(active={NODE: {}}, bountied={NODE}, done=set(), done_year=None, failed_attempts=Counter()),
            household=household, scenario=SimpleNamespace(year=100))
        self.polity = polity_host.build()
        self.knowledge = module_harness.build(Knowledge, views={"legacy_projects": self.state.projects},
                                              answers={RefreshDoneCaches: None}, seat=KnowledgeSeat())
        self.failed, self.applied, self.granted_staff, self.transfers = [], [], [], []
        policy = {"auto_open": auto_open, "auto_hire": hire_mode}
        module = self.module = projects_host.build(
            tree={NODE: {"name": "A school"}}, legacy_projects=self.state.projects, legacy_dice=SimpleNamespace(random=lambda: 0.5),
            alarm_of=lambda node: 2.0, state_interest=lambda node: 1.0, year=100, is_venture=lambda node_id: venture,
            mechanic=lambda name: {NODE: {"scholars": 1.0}} if name == "staff_grant" else {}, tech_effects=lambda node_id: None,
            automatic_policy=lambda name: policy[name], capability_sets=(frozenset(), frozenset(), {}))
        module.needs.send = self.send
        module.effective_risk = lambda node_id: 1.0 if fails else 0.0
        module._fail_attempt = lambda node_id, risk: self.failed.append((node_id, risk))
        module.goal_snapshot = lambda: snapshot
        module.reputation_gain_of = lambda node: 3.0
        module.opening_shortfall = lambda node_id: shortfall
        module.goal_effect_lines = lambda node_id, before: list(goal_lines)

    def send(self, command):
        if isinstance(command, ApplyTechEffects):
            self.applied.append(command.node_id)
            return None
        if isinstance(command, GrantStaff):
            self.granted_staff.append({"scholars": command.scholars})
            return None
        if isinstance(command, RecordGoalReached):
            self.goal_reached = (command.node_id, command.year)
            return None
        if isinstance(command, RevealFrom):
            return None
        if isinstance(command, LearnTechnique):
            return self.knowledge.learn_technique(command)
        if isinstance(command, CarryOutTransfers):
            self.transfers.append(command.node_id)
            return None
        if isinstance(command, GainReputation):
            return self.polity.gain_reputation(command)
        if isinstance(command, AddScandal):
            return self.polity.add_scandal(command)
        if isinstance(command, AddGovernance):
            return self.polity.add_governance(command)
        return event_stand_in.send(self, command)


def complete(game):
    game.module._complete(NODE)
    return game


# ---- a failing attempt goes to the failure rule and finishes nothing
game = complete(Finishing(fails=True))
check("a failing attempt is handed to the failure rule and the project is not finished",
      game.failed == [(NODE, 1.0)] and NODE not in game.state.projects.done and NODE in game.state.projects.active and kinds(game) == [], game.failed)

# ---- a finished concern that is not opened for the player
game = complete(Finishing(venture=True, auto_open=False))
check("a finished project is done, dated and no longer active", NODE in game.state.projects.done and NODE not in game.state.projects.active
      and game.state.projects.done_year == {NODE: 100} and "school" not in game.state.household.hour_allocations, game.state.projects)
check("its effects are applied once and its transfer paid", game.applied == [NODE] and game.transfers == [NODE], None)
check("a finished concern logs one completion and no shortfall when the free staff cover it", kinds(game) == ["project_completed"], kinds(game))
game = complete(Finishing(venture=True, shortfall=(5.0, 5.0, 0.0, 0.0)))
check("a finished concern the free staff cannot open logs the completion, then the shortfall", kinds(game) == ["project_completed", "opening_shortfall"], kinds(game))
game = complete(Finishing(venture=False))
check("a finished project that is not a concern logs the completion alone", kinds(game) == ["project_completed"], kinds(game))
game = complete(Finishing(venture=True, auto_open=True, shortfall=(5.0, 5.0, 0.0, 0.0)))
check("a concern the policy opens itself says nothing of a shortfall", kinds(game) == ["project_completed"], kinds(game))
game = complete(Finishing(goal_lines=["goal effect: literacy 10% -> 15%"]))
check("a completion that moves the goal logs a goal_effect line after the completion", kinds(game) == ["project_completed", "goal_effect"], kinds(game))
check("the goal reached is recorded for the project and year", game.goal_reached == (NODE, 100), None)
game = complete(Finishing())
check("the founder's reputation rises, and the alarm and the state's interest are booked", game.polity.seat.reputation == 5.0 + 3.0
      and game.polity.seat.scandal == 2.0 and game.polity.seat.gov == 1.0, None)
game = complete(Finishing(hire_mode=False))
check("without automatic hiring the work's staff grant is given", game.granted_staff == [{"scholars": 1.0}], game.granted_staff)
game = complete(Finishing(hire_mode=True))
check("with automatic hiring the grant is left to the staff ceiling", game.granted_staff == [], game.granted_staff)

# ---- the rules the log reads
severity_game = projects_host.build()
severity_game.goal_closure_ids = lambda: {"on_the_road"}
check("a small loss off the goal's road reads minor", severity_game.failure_severity("off_road", 30.0, 1000.0) == "minor", None)
check("the same loss on the goal's road reads major", severity_game.failure_severity("on_the_road", 30.0, 1000.0) == "major", None)
staff = projects_host.build(venture_hands=lambda node_id: (5.0, 5.0), venture_staff_free=lambda: (0.0, 9.0))
check("the opening shortfall is the concern's hands against the free staff", staff.opening_shortfall(NODE) == (5.0, 5.0, 0.0, 9.0), None)
staff = projects_host.build(venture_hands=lambda node_id: (5.0, 5.0), venture_staff_free=lambda: (50.0, 50.0))
check("no shortfall when the free staff cover it", staff.opening_shortfall(NODE) is None, None)

before = {"measures": {"literacy general": (0.10, True)}, "road_done": 3, "road_total": 9}
after = {"measures": {"literacy general": (0.15, True)}, "road_done": 4, "road_total": 9}


def goal_game(snapshot, done, closure):
    game = projects_host.build(tree={"top": {"name": "Top"}}, goal={"node": "top", "year": None, "years": {}}, legacy_fog=False, legacy_projects=SimpleNamespace(done=done))
    game.goal_snapshot = lambda: snapshot
    game.goal_closure_ids = lambda: closure
    return game


goal = goal_game(after, set(), {NODE})
lines = goal.goal_effect_lines(NODE, before)
check("a measure that moved gives a goal effect line and a node on the road adds the road line", len(lines) == 2 and lines[0].startswith("goal effect: literacy general"), lines)
check("with the goal itself done there is no road line", len(goal_game(after, {"top"}, {NODE}).goal_effect_lines(NODE, before)) == 1, None)
check("with no goal snapshot before there is nothing to report", goal_game(None, set(), set()).goal_effect_lines(NODE, None) == [], None)
