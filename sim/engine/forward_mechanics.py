"""One-line forwarders from `Sim` to the mechanics module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) itself."""
from sim.mechanics.api import rules


class ForwardMechanicsMixin:

    def running_with_mechanic(self, name):
        return [node_id for node_id, _parameters in self.view("running_mechanics")(name)]

    def best_corpus_node(self):
        """The corpus node that hedges best, or None if the tree has none."""
        best_first = self.view("corpus_nodes")()
        return best_first[0] if best_first else None

    @property
    def HAZARD_COUNTERS(self):
        """{kind: [(node or pseudo-source, share, label)]}: what each kind of harm is countered by.

        The mechanics module answers the node entries; the two own-mine sources are not nodes and their shares are
        declared with the hazards."""
        rows = self.view("hazard_counter_rows")()
        key = (self.HAZARD_EROSION_OWN_GOLD, self.HAZARD_EROSION_OWN_SILVER)
        cached = self.__dict__.get("_hazard_counters_cache")
        if cached is not None and cached[0] is rows and cached[1] == key:
            return cached[2]
        own = {"real_erosion": [(0, "_own_gold", key[0], "your own gold, dug not minted"),
                                (1, "_own_silver", key[1], "your own silver")]}
        counters = rules.hazard_counters(rows, own)
        self.__dict__["_hazard_counters_cache"] = (rows, key, counters)
        return counters
