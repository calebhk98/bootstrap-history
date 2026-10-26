"""One-line forwarders from the old `Sim` names of the actors to the actors module, for callers not yet in a module.

The registry handle `sim.actors` and the staff and concern figures are read by the engine's economy, the labour port, the screens
and the mods; each line goes when its last caller reads the view or sends the command itself."""
from sim.ledger.api import PayEdge, PayWages, ReceiveFromEdge


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

    # the three below forward to the ledger's commands until their callers send them themselves
    def pay_edge(self, edge_name, amount, purpose):
        """The acting seat's household pays a named edge: its loss is nobody's purse, and the edge keeps it."""
        self.send(PayEdge(edge_name, amount, purpose))

    def pay_wages(self, amount, purpose):
        """The acting seat's household pays wages: the home country's people receive them."""
        self.send(PayWages(amount, purpose))

    def receive_from_edge(self, edge_name, amount, purpose):
        """A named edge pays the acting seat's household."""
        self.send(ReceiveFromEdge(edge_name, amount, purpose))
