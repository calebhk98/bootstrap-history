"""One-line forwarders from `Sim` to the knowledge module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command itself."""
from sim.knowledge.api import RevealFrom


class ForwardKnowledgeMixin:

    def has(self, node_id):
        return node_id in self.view("techniques_held")()

    def corpus_hedge(self):
        return self.view("corpus_hedge")()

    def is_visible(self, node_id, _memo=None):
        return self.view("visibility")(node_id, _memo)

    def missing_prereq_message(self, missing, _memo=None):
        return self.view("prerequisite_message")(missing, _memo)

    def fog_scrub(self, text):
        return self.view("fog_scrub")(text)

    def fog_summary(self, node_id):
        return self.view("fog_summary")(node_id)

    def never_abandon(self, node_id):
        return self.view("never_abandon")[node_id]

    def reveal_from(self, node_id):
        self.send(RevealFrom(node_id))
