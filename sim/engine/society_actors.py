"""Actors other than the founder, run once a year inside the simulation."""
from .actors import ActorRegistry, SimWorld
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

    def advance_actors(self, year):
        """Give the country's government and every firm their year."""
        self.actors.ensure_government(str(self.civ.get("id")), self.civ.get("name", ""))
        self.actors.advance(SimWorld(self))
