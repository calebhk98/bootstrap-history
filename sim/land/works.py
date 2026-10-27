"""The constructions an actor has built, by tile, and what building more of one costs.

`LandWorld.works` is {tile: {construction node id: capacity}}, the register beside the ways: a built work belongs to the tile
where it stands. One unit of capacity is the node's ordinary size; each further unit at the same tile costs more (the scalable
institutions' convexity), so a larger work is dearer per unit than several small ones in different places. Nothing here is
specific to the founder: the acting seat's household pays.

A work is paid for when it is started and counts once its build time has passed. [temporary_heuristic]
The build time does not scale with capacity, and the crew is not drawn from the labour market's pools.
"""
from typing import Any, Dict, Tuple

from sim.agents.api import edges
from sim.ledger.api import PayEdge

from . import works_rules
from .commands import BuildWork, LoseWork


class Works:
    """Mixed into `Land`."""

    needs: Any
    world: Any

    def works_at(self, tile: str) -> Dict[str, float]:
        """{construction node id: capacity} built on a tile."""
        return dict(self.world.works.get(tile, {}))

    def work_capacity(self, node_id: str) -> float:
        """Capacity of a construction built across all tiles."""
        return sum(built.get(node_id, 0.0) for built in self.world.works.values())

    def work_quote(self, tile: str, node_id: str, capacity: float = 1.0) -> Dict[str, float]:
        """What adding `capacity` of a construction at a tile costs now: {money, years, capacity}."""
        have = self.world.works.get(tile, {}).get(node_id, 0.0)
        node = self.needs.tree_nodes()[node_id]
        money = works_rules.work_money(self.needs.project_cost_now(node_id), have, capacity,
                                       self.needs.legacy_constant["INSTITUTION_EXPANSION_CONVEXITY"])
        return {"money": money, "capacity": capacity, "years": float(node.get("build_yrs") or node.get("yrs") or 0.0)}

    def build_work(self, command: BuildWork) -> Tuple[bool, str]:
        """Build `capacity` of a known construction on a tile the nation holds. Answers (ok, text)."""
        needs = self.needs
        tile, node_id, capacity = command.tile, command.node, command.capacity
        refusal = works_rules.start_refusal(
            capacity, tile in set(needs.settlement_tiles()), node_id,
            node_id in needs.tree_nodes() and needs.is_venture[node_id],
            set(needs.techniques_held()) | set(needs.techniques_granted()),
            node_id in self.world.works_under_construction.get(tile, {}), tile)
        if refusal:
            return False, refusal
        quote = self.work_quote(tile, node_id, capacity)
        if not needs.can_pay(quote["money"]):
            return False, "%.2g of %s costs about %s; %s." % (
                capacity, node_id, needs.money_text(quote["money"], grouped=True), needs.afford_means())
        needs.send(PayEdge(edges.EDGE_BUILDERS, quote["money"], "building %s" % node_id))
        self.world.works_under_construction.setdefault(tile, {})[node_id] = [needs.year() + quote["years"], capacity]
        return True, "started %.2g of %s on %s for %s; it will take about %.1f years." % (
            capacity, node_id, tile, needs.money_text(quote["money"], grouped=True), quote["years"])

    def finish_works(self) -> None:
        """Count the works whose build time has passed on their tiles."""
        works_rules.finish_works(self.world.works_under_construction, self.world.works, self.needs.year())

    def lose_work(self, command: LoseWork) -> None:
        """Take up to `capacity` of a work away from a tile (destroyed, abandoned, sacked)."""
        works_rules.lose_work(self.world.works, command.tile, command.node, command.capacity)
