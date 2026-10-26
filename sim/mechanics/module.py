"""The mechanics module: lookups over the `mechanics` field of the loaded tree, and the effects they add up to.

It owns no state. It reads the tree, which techniques are held and which are running (views of owners that may not
have moved yet) and answers from an index it rebuilds whenever the tree object is replaced."""
from sim.assembly.api import Module

from . import rules


class Mechanics(Module):
    def setup(self):
        self._built = None   # (tree object, index, derived values); never saved

    # ---- the index, rebuilt when the tree object is replaced
    def _index(self):
        nodes = self.needs.tree_nodes()
        built = self._built
        if built is None or built[0] is not nodes:
            built = self._built = (nodes, rules.mechanics_index(nodes), {})
        return built[1], built[2]

    def _derived(self, key, build):
        index, derived = self._index()
        if key not in derived:
            derived[key] = build(index)
        return derived[key]

    def mechanic(self, name):
        """{node id: parameters} of the nodes declaring mechanic `name`, in id order."""
        return self._index()[0].get(name, {})

    def running_mechanics(self, name):
        """[(node id, parameters)] of the running nodes that declare mechanic `name`."""
        running = self.needs.running
        return [(node_id, parameters) for node_id, parameters in self.mechanic(name).items() if running[node_id]]

    def capability_sets(self):
        """(capability ids, scalable ids, {id: lost benefit}) of the `capability` mechanic."""
        return self._derived("capability_sets", lambda index: rules.capability_sets(index.get("capability", {})))

    def staff_capacity_sources(self):
        return rules.staff_capacity_sources(self.needs.tree_nodes())

    def room_sources(self):
        return rules.room_sources(self.effect_terms("room_places"))

    def labour_productivity_sources(self):
        return rules.labour_productivity_sources(self.effect_terms("labour_productivity"))

    def hazard_counter_rows(self):
        """{kind: [(order, node, share, label)]} from the nodes' `hazard_counters`."""
        return self._derived("hazard_counters", lambda index: rules.hazard_counter_rows(index.get("hazard_counters", {})))

    # ---- effect channels: nodes declare `{channel: {"flat"|"per_unit"|"per_sqrt_unit": v, ...}}`
    def effect_terms(self, channel):
        """[(node id, spec)] declaring `channel`, in (order, id) sequence."""
        return self._derived("terms:" + channel, lambda index: rules.ordered_terms(index.get(channel, {})))

    def effect_holds(self, node_id, spec):
        """Whether a declared effect is switched on: operating, or merely built if the spec says gate `has`."""
        if spec.get("gate") == "has":
            return node_id in self.needs.techniques_held()
        return self.needs.running[node_id]

    def effect_value(self, node_id, spec):
        """The size of one node's effect."""
        return rules.effect_size(spec, lambda: self.needs.institution_units[node_id], self.needs.money_per_labour_hour)

    def effects_in_force(self, channel):
        """[(node id, spec)] declaring effect `channel` that are switched on, in declared order."""
        return [(node_id, spec) for node_id, spec in self.effect_terms(channel) if self.effect_holds(node_id, spec)]

    def effect_values(self, channel):
        """[(node id, size)] for every node whose `channel` effect is switched on, one per `group`."""
        return rules.grouped_values(self.effect_terms(channel), self.effect_holds, self.effect_value)

    def effect_sum(self, channel, start=0.0):
        return rules.sum_in_order(self.effect_values(channel), start)

    def effect_factor(self, channel, start=1.0, exponent=None):
        return rules.factor_product(self.effect_terms(channel), self.effect_holds,
                                    lambda node_id: self.needs.institution_units[node_id], start, exponent)

    def effect_best(self, channel):
        """(node id, spec) of the switched-on `channel` effect with the highest `tier`, or None."""
        return rules.best_by_tier(self.effect_terms(channel), self.effect_holds)

    # ---- corpus (the hedge against a sacking), patrons and schooling
    def corpus_nodes(self):
        """Ids of the corpus nodes, highest rank first."""
        return rules.corpus_best_first(self.mechanic("corpus"))

    def corpus_hedge_tiers(self):
        return rules.corpus_hedge_tiers(self.mechanic("corpus"))

    def corpus_dispersed(self, node_id):
        """Whether a corpus node's copies sit beyond one site's reach (a sack cannot take them)."""
        return bool((self.mechanic("corpus").get(node_id) or {}).get("dispersed"))

    def corpus_diffusion_pace(self):
        """Diffusion pace of the best corpus node currently operating (1.0 if none)."""
        corpus = self.mechanic("corpus")
        for node_id in rules.corpus_best_first(corpus):
            if self.needs.running[node_id]:
                return corpus[node_id]["diffusion_pace"]
        return 1.0

    def approval_patron(self, gate):
        """The patron node whose backing lifts the state's `gate` ("wary" or "opposed") on a project, or None."""
        return rules.approval_patron(self.mechanic("state_approval"), gate)

    def school_node(self):
        """The node whose operation is required for any schooling to happen, or None."""
        return rules.school_node(self.effect_terms("schooling_flow"))

    def patrons_lost_to_eminence(self):
        """Patron nodes an eminent household can lose to a quarrel, highest tier first."""
        return rules.patrons_lost_to_eminence(self.mechanic("patron_lost_to_eminence"), self.mechanic("patron"))
