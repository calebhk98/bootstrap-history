"""The constructions an actor has built, by tile, and what building more of one costs.

`state.economy.works` is {tile: {construction node id: capacity}}, the register beside the ways of
ways.py: a built work belongs to the tile where it stands. One unit of capacity is the node's ordinary
size; each further unit at the same tile costs more (the scalable institutions' convexity), so a larger
work is dearer per unit than several small ones in different places. Nothing here is specific to the
founder: it asks for the paying actor's household.

A work is paid for when it is started and counts once its build time has passed. [temporary_heuristic]
The build time does not scale with capacity, and the crew is not drawn from the labour market's pools.
"""
from sim.agents.api import edges
from .units_prose import money_text


class WorksMixin:

    def works_at(self, tile):
        """{construction node id: capacity} built on a tile."""
        return dict(self.state.economy.works.get(tile, {}))

    def work_capacity(self, node_id):
        """Capacity of a construction built across all tiles."""
        return sum(built.get(node_id, 0.0) for built in self.state.economy.works.values())

    def _work_cost_curve(self, units):
        return units + self.INSTITUTION_EXPANSION_CONVEXITY * 0.5 * max(0.0, units - 1.0) ** 2

    def work_quote(self, tile, node_id, capacity=1.0):
        """What adding `capacity` of a construction at a tile costs now: {money, years, capacity}."""
        have = self.state.economy.works.get(tile, {}).get(node_id, 0.0)
        units = self._work_cost_curve(have + capacity) - self._work_cost_curve(have)
        node = self.nodes[node_id]
        return {"money": self.project_cost_now(node_id) * units, "capacity": capacity,
                "years": float(node.get("build_yrs") or node.get("yrs") or 0.0)}

    def build_work(self, tile, node_id, capacity=1.0):
        """Build `capacity` of a known construction on a tile the nation holds. Returns (ok, message)."""
        if capacity <= 0:
            return False, "the capacity to build must be above nothing."
        if tile not in set(self.labour.settlement_tiles()):
            return False, "you can build only on a tile your nation holds."
        if node_id not in self.nodes or not self.is_venture(node_id):
            return False, "%s is not something that can be built and kept up." % node_id
        known = set(self.state.projects.done) | set(self.state.projects.granted)
        if node_id not in known:
            return False, "your people do not know how to build %s yet." % node_id
        if node_id in self.state.economy.works_under_construction.get(tile, {}):
            return False, "%s is already being built on %s." % (node_id, tile)
        quote = self.work_quote(tile, node_id, capacity)
        from . import purchase_rule
        if not purchase_rule.can_pay(self, quote["money"]):
            return False, "%.2g of %s costs about %s; %s." % (
                capacity, node_id, money_text(quote["money"], self, grouped=True), purchase_rule.afford_means())
        self.pay_edge(edges.EDGE_BUILDERS, quote["money"], "building %s" % node_id)
        self.state.economy.works_under_construction.setdefault(tile, {})[node_id] = [self.state.scenario.year + quote["years"], capacity]
        return True, "started %.2g of %s on %s for %s; it will take about %.1f years." % (
            capacity, node_id, tile, money_text(quote["money"], self, grouped=True), quote["years"])

    def finish_works(self):
        """Count the works whose build time has passed on their tiles."""
        pending = self.state.economy.works_under_construction
        for tile in sorted(pending):
            for node_id in sorted(pending[tile]):
                due_year, capacity = pending[tile][node_id]
                if due_year <= self.state.scenario.year:
                    built = self.state.economy.works.setdefault(tile, {})
                    built[node_id] = built.get(node_id, 0.0) + capacity
                    del pending[tile][node_id]
            if not pending[tile]:
                del pending[tile]

    def lose_work(self, tile, node_id, capacity):
        """Take up to `capacity` of a work away from a tile (destroyed, abandoned, sacked)."""
        built = self.state.economy.works.get(tile, {})
        left = built.get(node_id, 0.0) - capacity
        if left > 1e-9:
            built[node_id] = left
            return
        built.pop(node_id, None)
        if not built:
            self.state.economy.works.pop(tile, None)
