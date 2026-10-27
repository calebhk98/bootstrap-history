"""One-line forwarders from the old `Sim` names of the actors to the actors module, for callers not yet in a module.

The registry handle `sim.actors` and the staff and concern figures are read by the engine's economy, the labour port, the screens
and the mods; each line goes when its last caller reads the view or sends the command itself."""


class ActorsForwardsMixin:

    @property
    def actors(self):
        """The registry of governments and firms."""
        return self.view("cast")()

    def edge(self, name):
        """The named edge a posting names when its other side is not an actor the simulation models."""
        return self.view("legacy_edge_account")[name]

    def state_treasury(self):
        return self.view("state_treasury")()

    def actor_staff_fte(self, trade):
        return self.view("actor_staff")[trade]

    def actor_staff_nationwide(self, trade):
        return self.view("actor_staff_nationwide")[trade]

    def actor_staff_total(self):
        return self.view("actor_staff_total")()

    def actor_concerns_in(self, category):
        return self.view("concern_counts")[category]

    def actor_market_version(self):
        return self.view("concern_versions")()[0]

    def concern_set_version(self):
        return self.view("concern_versions")()[1]
