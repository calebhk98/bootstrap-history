"""Actors other than the founder, run once a year inside the simulation."""
from sim.agents import ActorRegistry, SimWorld, ledger
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
            registry = ActorRegistry(state.actors)
            self._actor_registry = registry
        return registry

    def actor_staff_fte(self, trade):
        """People of this trade that firms and governments employ: they come out of the
        same reachable pool the founder hires from."""
        state = self.state.actors
        if state is None or not state.records:
            return 0.0
        return self.actors.staff_fte(trade)

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
        """The government actor of the founder's civilisation."""
        return self.actors.ensure_government(str(self.civ.get("id")), self.civ.get("name", ""))

    def pay_state(self, amount, purpose):
        """The household pays the state: the founder's loss is the treasury's gain."""
        ledger.transfer(self.household, self.state_treasury(), amount, purpose)

    def advance_actors(self, year):
        """Give the country's government and every firm their year."""
        self.state_treasury()
        self.update_capital_market()
        self.actors.advance(SimWorld(self))
