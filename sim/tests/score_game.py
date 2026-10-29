"""A stand-in game for the score: exactly the fields and methods `score_report` and `final_report` read, with plain
values the test sets, so each scoring rule is called on inputs the test builds (no game is run)."""
from types import SimpleNamespace

from sim.engine.state import FounderState


from sim.tests.ui_stand_in import FactViews


class ScoreGame(FactViews):
    """What `score_report` reads of a game. Every number is a plain attribute."""

    CAPABILITY_INSTITUTIONS = frozenset({"workshop_first", "school_founded", "identity_cover"})
    SCALABLE_INSTITUTIONS = frozenset({"workshop_first", "school_founded"})

    def __init__(self, nodes, goal="goal", start_year=100, horizon_years=500):
        self.nodes = nodes
        self.goal = goal
        self.goal_year = None
        self.cfg = {"start_year": start_year, "horizon_years": horizon_years}
        self.year = start_year
        self.fog = False
        self.dead_reason = None
        self.done = set()
        self.granted = set()
        self.operating = set()
        self.failed_attempts = {}
        self.capital = 1000.0
        self.reputation = 10.0
        self.scandal = 0.0
        self.forgotten = {}
        self.insolvent_years = 0
        self.interest_paid = 0.0
        self.slaves = 0
        self.manumitted_total = 0
        self.founder_alive = True
        self.ever_closed_for_staff = set()
        self.units = {}
        self.literacy_values = {"literacy_general": 0.05, "literacy_elite": 0.5}
        self.general_ceiling = 0.2
        self.elite_ceiling = 0.8
        self.headcount = 10.0
        self.wage = 100.0
        self.state = SimpleNamespace(founder=FounderState(),
                                     interface={}, seat_progress=SimpleNamespace(score_last_seen=None))
        self._goal_critical_floor = 20.0
        self.shut_for_staff = {}
        self.labour = SimpleNamespace(
            headcount=lambda: self.headcount,
            base_annual_wage=lambda trade: self.wage,
            market=SimpleNamespace(in_current_money=lambda amount: amount))

    @property
    def staff(self):
        return {"slaves": self.slaves, "manumitted_total": self.manumitted_total}

    def literacy(self, name):
        return self.literacy_values[name]

    def literacy_ceiling_general(self):
        return self.general_ceiling

    def literacy_ceiling_elite(self):
        return self.elite_ceiling

    def institution_unit_ceiling(self, institution_id):
        return 4.0

    def institution_units(self, institution_id):
        return self.units.get(institution_id, 0.0)

    def running(self, institution_id):
        return institution_id in self.operating

    def has(self, institution_id):
        return institution_id in self.done
