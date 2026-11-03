"""What the labour package reads of the game: `send` and the acting seat's own state here, and one reader group per owning module
(world_reads.py): `scenario`, `knowledge`, `finance`, `people`, `trades`, `actors`, `ventures`, `directors`, `game`, `standing`, plus `projects` and
`economy` below; the commands it sends are `commands` (world_commands.py).

`Labour` (sim/labour/) asks this object where it used to ask the engine. Every fact comes from a named view of its owner
and every change to a fact another module owns is that owner's command. What is still handed out live: the project sets the views of knowledge and projects return, and the game
a mod's provider is handed."""
from sim.agents.api import edges

from .world_commands import WorldCommands
from .world_reads_game import GameReads, StandingReads
from .world_reads import ActorReads, DirectorReads, FinanceReads, KnowledgeReads, PeopleReads, ScenarioReads, TradeReads, VentureReads


class WorkforceWorld:

    # the named edges labour's postings name as their counterparty
    EDGE_WORKERS = edges.EDGE_WORKERS
    EDGE_SLAVE_TRADERS = edges.EDGE_SLAVE_TRADERS
    EDGE_EMPLOYERS = edges.EDGE_EMPLOYERS

    def __init__(self, needs, owner, parts):
        self._needs = needs
        self._owner = owner          # the workforce module: its seat and world state
        self._parts = parts          # its parts, which answer the rest
        self.economy = AgentEconomyReads(needs)    # what the agent economy answers, as the views the module declares give it
        self.projects = ProjectReads(needs)        # the acting seat's project sets, each asked of its owner when read
        self.commands = WorldCommands(needs, parts)
        self.scenario = ScenarioReads(needs)
        self.knowledge = KnowledgeReads(needs)
        self.finance = FinanceReads(needs)
        self.people = PeopleReads(needs)
        self.trades = TradeReads(needs, parts)
        self.actors = ActorReads(needs)
        self.ventures = VentureReads(needs)
        self.directors = DirectorReads(needs)
        self.game = GameReads(needs)
        self.standing = StandingReads(needs)

    def send(self, command):
        """Apply a command through the module that owns it."""
        return self._needs.send(command)

    @property
    def workforce(self):
        """The acting seat's people and hours: the module's own seat state, written only by labour and the module."""
        return self._owner.seat

    @property
    def society(self):
        """The society's labour hours by trade: the module's own world state."""
        return self._owner.world


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

    def agent_wage_at(self, trade, tile):
        """Money one hour of the trade costs a bid on `tile` (the wage of the tile's labour area, else the unpriced-trade
        wage); None until the game's money is priced at the economy."""
        if self._needs.agent_unskilled_wage() is None:
            return None
        return self._needs.agent_wage_at(trade, tile)

    def agent_hours_offered_at(self, trade, tile):
        """Hours of the trade households offered in `tile`'s labour area at the last clearing; None before one."""
        return self._needs.agent_hours_offered_at(trade, tile)

    def agent_working_hours(self):
        """The hours a person-year counts in the running economy; None while it opens."""
        return self._needs.agent_working_hours()

    def agent_trades(self):
        """The trades the agent economy holds; None until it opens."""
        if self._needs.agent_unskilled_wage() is None:
            return None
        return self._needs.agent_trades()

    def agent_country(self, country):
        return self._needs.agent_country[country]

    def agent_prices(self):
        return self._needs.agent_prices()
