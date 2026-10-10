"""Actors other than the founder, run once a year inside the simulation."""
from sim.agents.api import ActorRegistry, ledger, payroll, SOLDIER_TRADE
from .actor_kinds_data import register_mod_actor_kinds
from .agents_port import SimWorld
from .agents_port_cast import seed_opening_cast
from .state import ActorsState


class ActorsMixin:

    @property
    def actors(self):
        """Registry of governments and firms, rebuilt whenever the state object is replaced."""
        state = self.state
        if state.actors is None:
            state.actors = ActorsState()
        registry = self.__dict__.get("_actor_registry")
        if registry is None or registry.state is not state.actors:
            register_mod_actor_kinds()
            registry = ActorRegistry(state.actors)
            self._actor_registry = registry
        return registry

    def edge(self, name):
        """The named edge a posting names when its other side is not an actor the simulation models."""
        if self.state.actors is None:
            self.state.actors = ActorsState()
        return self.state.actors.edge(name)

    def pay_edge(self, edge_name, amount, purpose):
        """The founder's household pays a named edge: its loss is nobody's purse, and the edge keeps it."""
        ledger.transfer(self.state.household, self.edge(edge_name), amount, purpose)

    def pay_wages(self, amount, purpose):
        """The founder's household pays wages: the home country's people receive them."""
        payroll.pay_wages(self.actors, self.state.household, amount, purpose, self)

    def receive_from_edge(self, edge_name, amount, purpose):
        """A named edge pays the founder's household."""
        ledger.transfer(self.edge(edge_name), self.state.household, amount, purpose)

    def actor_staff_fte(self, trade):
        """People of this trade that firms and governments employ: they come out of the
        same reachable pool the founder hires from."""
        state = self.state.actors
        if state is None or not state.records:
            return 0.0
        return self.actors.staff_fte(trade)

    def actor_staff_nationwide(self, trade):
        """People of this trade that firms and governments hold nationwide. Staff in the founder's
        reachable pool is the slice the actors drew from it; the government's army is its whole
        force, so that one trade reads the army in place of the government's slice."""
        state = self.state.actors
        if state is None or not state.records:
            return 0.0
        people = self.actor_staff_fte(trade)
        if trade == SOLDIER_TRADE:
            record = state.records.get("government:" + str(self.civ.get("id")))
            if record is not None:
                people += record.army - record.workforce.get(trade, 0.0)
        return max(0.0, people)

    def actor_staff_total(self):
        """People of every trade that firms and governments employ."""
        state = self.state.actors
        if state is None or not state.records:
            return 0.0
        return sum(self.actors.staff_by_trade().values())

    def actor_supply(self, material):
        """Tonnes of `material` that firms and governments sold into the market this year, summed
        over every actor; the founder's own sales are not included."""
        return self.goods_market.others_sold_tonnes(self._material_tag(material)[0])

    def actor_demand(self, commodity):
        """Tonnes of a commodity that governments bought on the market this year."""
        return self.goods_market.others_bought_tonnes(commodity)

    def state_levy_rates(self):
        """(requisition, office) share of income the state takes at full notice; nothing
        before the state has budgeted a year."""
        state = self.state.actors
        record = None if state is None else state.records.get("government:" + str(self.civ.get("id")))
        if record is None:
            return 0.0, 0.0
        return record.levy_requisition_rate, record.levy_office_rate

    def state_military_ask(self, taxable, scale):
        """What the state asks of one militarily useful taxpayer in arms this year."""
        return self.state_treasury().military_ask(taxable, scale, SimWorld(self))

    def actor_concerns_in(self, category):
        """How many concerns in a goods category actors run, each sharing the founder's market."""
        state = self.state.actors
        if state is None or not state.records:
            return 0
        return self.actors.concerns_in(category, self.nodes)

    def actor_market_version(self):
        """Changes whenever the set of concerns actors run does, for caches that read it."""
        state = self.state.actors
        if state is None or not state.records:
            return 0
        return self.actors.version[0]

    def state_treasury(self):
        """The government actor of the acting seat's country: the founder's civilisation unless the seat belongs
        to a partner country that has a government of its own in the cast."""
        seed_opening_cast(self)  # a bare record made first would keep the cast from giving it its place and kind
        country = self.acting_country()
        if country is not None:
            government = self.actors.government_of(country)
            if government is not None:
                return government
        return self.actors.ensure_government(str(self.civ.get("id")), self.civ.get("name", ""))

    def pay_state(self, amount, purpose):
        """The household pays the state: the founder's loss is the treasury's gain."""
        with self.coin_carriage_listening():
            ledger.transfer(self.household, self.state_treasury(), amount, purpose)

    def advance_actors(self, year):
        """Give every actor its year: the countries, players, firms, traders and bodies of people. Coin moved
        between actors in different places pays carriage meanwhile."""
        with self.coin_carriage_listening():
            self._advance_actors_year(year)

    def _advance_actors_year(self, year):
        seed_opening_cast(self)
        self.state_treasury()
        self.refresh_lender_offers()
        self.actors.advance(SimWorld(self))
        self.accrue_industry_experience()
        self.charge_actors_for_keeping_coin()
        self.charge_actors_for_theft()
