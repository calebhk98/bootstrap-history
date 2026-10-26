"""Complaints 81, 83 and 127: what a finished or failed project logs, by kind and facts. `CompletionMixin._complete`, `failure_severity`,
`opening_shortfall` and `goal_effect_lines` run on a stand-in `self` carrying only what they read; the severity, shortfall and goal
movement rules are test_completion_messaging."""

QUICK_TOPIC = True

from collections import Counter
from types import SimpleNamespace

from .harness import check

from sim.engine.projects_completion import CompletionMixin
from sim.knowledge.api import KnowledgeSeat, LearnTechnique, RefreshDoneCaches
from sim.knowledge.module import Knowledge
from sim.refusal import cause_of
from sim.tests import event_stand_in, module_harness

NODE = "school"


def kinds(game):
    return [cause_of(line) for _year, line in game.state.household.log]


class Finishing:
    """A stand-in game with one active project, `school`, whose attempt is about to end."""

    def send(self, command):
        if isinstance(command, LearnTechnique):
            return self.knowledge.learn_technique(command)
        return event_stand_in.send(self, command)

    def __init__(self, fails=False, venture=True, auto_open=False, shortfall=None, goal_lines=(), snapshot=None, hire_mode=False):
        household = SimpleNamespace(log=[], hour_allocations={"school": 1.0}, reputation=0.0, scandal=0.0)
        self.state = SimpleNamespace(
            projects=SimpleNamespace(active={NODE: {}}, bountied={NODE}, done=set(), done_year=None, failed_attempts=Counter()),
            household=household, scenario=SimpleNamespace(year=100), governance=SimpleNamespace(gov=0.0))
        self.knowledge = module_harness.build(Knowledge, views={"legacy_projects": self.state.projects},
                                              answers={RefreshDoneCaches: None}, seat=KnowledgeSeat())
        self.nodes = {NODE: {"name": "A school"}}
        self.rng = SimpleNamespace(random=lambda: 0.5)
        self.fails, self.venture, self.auto_open, self.shortfall = fails, venture, auto_open, shortfall
        self.goal_lines, self.snapshot, self.hire_mode = list(goal_lines), snapshot, hire_mode
        self.REPUTATION_CEILING = 100.0
        self.NOT_OPERATING_BENEFIT = {}
        self.policy = {"auto_open": auto_open, "auto_hire": hire_mode}
        self.manual = True
        self._tech_effects = {}
        self.failed, self.applied, self.granted_staff, self.transfers = [], [], [], []

    def effective_risk(self, node_id):
        return 1.0 if self.fails else 0.0

    def _fail_attempt(self, node_id, risk):
        self.failed.append((node_id, risk))

    def goal_snapshot(self):
        return self.snapshot

    def carry_out_transfers(self, node_id):
        self.transfers.append(node_id)

    def alarm_of(self, node):
        return 2.0

    def apply_tech_effects(self, node_id):
        self.applied.append(node_id)

    def reveal_from(self, node_id):
        pass

    def reputation_gain_of(self, node):
        return 3.0

    def state_interest(self, node):
        return 1.0

    def mechanic(self, node_id, name):
        return {"scholars": 1.0} if name == "staff_grant" else {}

    @property
    def labour(self):
        return SimpleNamespace(grant_staff=lambda **grant: self.granted_staff.append(grant))

    def is_venture(self, node_id):
        return self.venture

    def opening_shortfall(self, node_id):
        return self.shortfall

    def goal_effect_lines(self, node_id, before):
        return self.goal_lines

    def record_goal_reached(self, node_id, year):
        self.goal_reached = (node_id, year)


def complete(game):
    CompletionMixin._complete(game, NODE)
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
check("the founder's reputation rises, and the alarm and the state's interest are booked", game.state.household.reputation == 3.0
      and game.state.household.scandal == 2.0 and game.state.governance.gov == 1.0, None)
game = complete(Finishing(hire_mode=False))
check("without automatic hiring the work's staff grant is given", game.granted_staff == [{"scholars": 1.0}], game.granted_staff)
game = complete(Finishing(hire_mode=True))
check("with automatic hiring the grant is left to the staff ceiling", game.granted_staff == [], game.granted_staff)

# ---- the rules the log reads
severity_game = SimpleNamespace(goal_closure_ids=lambda: {"on_the_road"}, MINOR_FAILURE_SHARE=0.05, GOAL_PATH_FAILURE_WEIGHT=2.0)
check("a small loss off the goal's road reads minor", CompletionMixin.failure_severity(severity_game, "off_road", 30.0, 1000.0) == "minor", None)
check("the same loss on the goal's road reads major", CompletionMixin.failure_severity(severity_game, "on_the_road", 30.0, 1000.0) == "major", None)
staff = SimpleNamespace(venture_hands=lambda node_id: (5.0, 5.0), venture_staff_free=lambda: (0.0, 9.0))
check("the opening shortfall is the concern's hands against the free staff", CompletionMixin.opening_shortfall(staff, NODE) == (5.0, 5.0, 0.0, 9.0), None)
staff = SimpleNamespace(venture_hands=lambda node_id: (5.0, 5.0), venture_staff_free=lambda: (50.0, 50.0))
check("no shortfall when the free staff cover it", CompletionMixin.opening_shortfall(staff, NODE) is None, None)

before = {"measures": {"literacy general": (0.10, True)}, "road_done": 3, "road_total": 9}
after = {"measures": {"literacy general": (0.15, True)}, "road_done": 4, "road_total": 9}
goal = SimpleNamespace(goal_snapshot=lambda: after, goal="top", goal_closure_ids=lambda: {NODE}, fog=False, state=SimpleNamespace(projects=SimpleNamespace(done=set())))
lines = CompletionMixin.goal_effect_lines(goal, NODE, before)
check("a measure that moved gives a goal effect line and a node on the road adds the road line", len(lines) == 2 and lines[0].startswith("goal effect: literacy general"), lines)
goal.state.projects.done = {"top"}
check("with the goal itself done there is no road line", len(CompletionMixin.goal_effect_lines(goal, NODE, before)) == 1, None)
check("with no goal snapshot before there is nothing to report", CompletionMixin.goal_effect_lines(
    SimpleNamespace(goal_snapshot=lambda: None, goal="top", goal_closure_ids=lambda: set(), fog=False, state=goal.state), NODE, None) == [], None)
