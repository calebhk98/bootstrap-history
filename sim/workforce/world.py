"""What the labour package reads of the game: `send` and the acting seat's own state here, and one reader group per owning module
(world_reads.py): `scenario`, `knowledge`, `finance`, `people`, `trades`, `actors`, plus `projects` and `economy` below.

`Labour` (sim/labour/) asks this object where it used to ask the engine. Every fact comes from a named view of its owner
and every change to a fact another module owns is that owner's command. What is still handed out live: the game's random
source (`rng`, shared by every module that draws), the project sets the views of knowledge and projects return, and the game
a mod's provider is handed."""
from sim.agents.api import edges
from sim.seats.api import RememberGoalClosure

from .commands_bondage import NoteBuyRefusal
from .world_reads import ActorReads, FinanceReads, KnowledgeReads, PeopleReads, ScenarioReads, TradeReads


class WorkforceWorld:

    # the named edges labour's postings name as their counterparty
    EDGE_WORKERS = edges.EDGE_WORKERS
    EDGE_SLAVE_TRADERS = edges.EDGE_SLAVE_TRADERS
    EDGE_EMPLOYERS = edges.EDGE_EMPLOYERS

    def __init__(self, needs, owner, parts):
        self._needs = needs
        self._owner = owner          # the workforce module: its seat and world state
        self._parts = parts          # its parts, which answer the rest
        self._economy = AgentEconomyReads(needs)
        self._projects = ProjectReads(needs)
        self.scenario = ScenarioReads(needs)
        self.knowledge = KnowledgeReads(needs)
        self.finance = FinanceReads(needs)
        self.people = PeopleReads(needs)
        self.trades = TradeReads(needs, parts)
        self.actors = ActorReads(needs)

    def send(self, command):
        """Apply a command through the module that owns it."""
        return self._needs.send(command)

    def reputation(self):
        return self._needs.standing()["reputation"]

    @property
    def founder_alive(self):
        return self._needs.founder()["alive"]

    @property
    def workforce(self):
        """The acting seat's people and hours: the module's own seat state, written only by labour and the module."""
        return self._owner.seat

    @property
    def year(self):
        return self._needs.year()

    @property
    def policy(self):
        """The acting seat's standing policy switches (read here, never written)."""
        return self._needs.founder()["policy"]

    @property
    def society(self):
        """The society's labour hours by trade: the module's own world state."""
        return self._owner.world

    @property
    def projects(self):
        """The acting seat's project sets (done, operating, in hand, granted), each asked of its owner when read."""
        return self._projects

    @property
    def bondage_years_left(self):
        return self._needs.debt_status()["bondage_years_left"]

    @property
    def rng(self):
        """The game's random source (shared and live: every draw moves the stream every other module draws from)."""
        return self._needs.game_random()

    @property
    def staff_scale(self):
        """The share of the institutional staff ceiling the acting seat's income can pay, as `staff_capacity` last worked it out."""
        return self._parts.core.staff_scale()

    @staff_scale.setter
    def staff_scale(self, scale):
        self._parts.core.set_staff_scale(scale)

    def remember_goal_closure(self, closure):
        """Keep what the goal needs, once worked out."""
        self._needs.send(RememberGoalClosure(closure))

    def note_buy_refusal(self, refusal):
        """Keep why the acting seat's purchase of people was refused, for the screen that asked."""
        self._parts.core.note_buy_refusal(NoteBuyRefusal(refusal))

    def money_text(self, amount, grouped=False, short=False):
        """A sum in the civilisation's coin as the player's chosen unit writes it."""
        return self._needs.money_text(amount, grouped, short)

    def plain_number(self, value, digits=0):
        """A count, a number of people or of hours."""
        return self._needs.plain_number(value, digits)

    @property
    def economy(self):
        """What the agent economy answers, as the views the module declares give it."""
        return self._economy


class ProjectReads:
    """The acting seat's project sets, each asked of the view that owns it every time it is read (the sets are the live ones)."""

    def __init__(self, needs):
        self._needs = needs

    @property
    def done(self):
        return self._needs.techniques_held()

    @property
    def operating(self):
        return self._needs.operating()

    @property
    def active(self):
        return self._needs.active_projects()

    @property
    def granted(self):
        return self._needs.techniques_granted()

    @property
    def done_year(self):
        return self._needs.done_year()


class AgentEconomyReads:
    """The agent economy's answers labour asks for, each a view of the module's needs."""

    def __init__(self, needs):
        self._needs = needs

    def unskilled_wage(self):
        """Money one hour of the unskilled trade is paid in the agent economy; None until the game's money is priced at it."""
        return self._needs.agent_unskilled_wage()

    def agent_people_by_trade(self):
        return self._needs.agent_people_by_trade()

    def agent_people_by_tile_and_trade(self):
        return self._needs.agent_people_by_tile_and_trade()

    def agent_idle_hours_by_trade(self):
        """{trade: (hours offered and not hired last year, hours offered)} nationwide."""
        return self._needs.agent_idle_hours_by_trade()

    def agent_wage_per_hour(self, trade):
        return self._needs.agent_wage[trade]

    def agent_trades(self):
        """The trades the agent economy holds; None until it opens."""
        if self._needs.agent_unskilled_wage() is None:
            return None
        return self._needs.agent_trades()

    def agent_country(self, country):
        return self._needs.agent_country[country]

    def agent_prices(self):
        return self._needs.agent_prices()
