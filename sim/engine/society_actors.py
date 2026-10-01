"""Actors other than the founder, run once a year inside the simulation."""
from .actors import ActorRegistry, SimWorld, ledger
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

    def state_treasury(self):
        """The government actor of the founder's civilisation."""
        return self.actors.ensure_government(str(self.civ.get("id")), self.civ.get("name", ""))

    def pay_state(self, amount, purpose):
        """The household pays the state: the founder's loss is the treasury's gain."""
        ledger.transfer(self.household, self.state_treasury(), amount, purpose)

    def advance_actors(self, year):
        """Give the country's government and every firm their year."""
        self.state_treasury()
        self.actors.advance(SimWorld(self))
