"""A node can require that a built work be running, not merely known.

`requires_running` on a node lists the ids of works (ventures) that must be built and open. It
gates beginning the node, switches the node's effects off while a work is shut (`running`), and
closes the node when it is open as the work closes. `requires_ways` ({way: kilometres}) asks for a
length of road or railway the actor has built (sim/engine/ways.py). Nothing here names a node.
"""
from .blockers import blocker_kind


@blocker_kind("closed")
def check_running_gates(self, node_id, node, ignore_trade, _memo, _why):
    """Refuse a node whose required works are not running; the refusal names the remedy."""
    if not self.gate_blocked(node_id):
        return None
    return False, (self.running_gate_refusal(node_id) if _why else None)


class RunningGatesMixin:

    CLOSED_GATE_LAPSED = "gate_lapsed"

    def unmet_running_gates(self, node_id):
        """The works `node_id` requires running that are not, in the order the node lists them."""
        needed = self.nodes[node_id].get("requires_running")
        if not needed:
            return []
        projects = self.state.projects
        return [work for work in needed if work not in projects.done or not self.running(work)]

    def ways_short(self, node_id):
        """{way: kilometres still to build} of what `requires_ways` asks beyond what is built."""
        asked = self.nodes[node_id].get("requires_ways")
        if not asked:
            return {}
        short = {way: km - self.built_way_km(way) for way, km in sorted(asked.items())}
        return {way: gap for way, gap in short.items() if gap > 0.0}

    def gate_blocked(self, node_id):
        """Whether a work or a length of way the node requires is missing."""
        return bool(self.unmet_running_gates(node_id) or self.ways_short(node_id))

    def running_gate_text(self, unmet, ways_short=None):
        """What to tell a player whose start or opening waits on works that are not running."""
        parts = []
        for work in unmet:
            if not self._visible_to_player(work):
                parts.append("a work you have not heard of")
            elif self.has(work):
                parts.append("%s is built but shut ('open %s' or 'restore %s')" % (work, work, work))
            else:
                parts.append("%s is not built yet" % work)
        parts += ["%.3g km more %s must be built" % (gap, way) for way, gap in sorted((ways_short or {}).items())]
        return "it needs a work that is running: " + "; ".join(parts)

    def running_gate_refusal(self, node_id):
        """The sentence refusing to open `node_id` while a work it needs is not running, else None."""
        unmet, short = self.unmet_running_gates(node_id), self.ways_short(node_id)
        return self.running_gate_text(unmet, short) if unmet or short else None

    def _running_gate_index(self):
        """({work id: sorted ids that require it running}, ids that require something), per tree."""
        cached = self.__dict__.get("_running_gate_cache")
        if cached is not None and cached[0] is self.nodes:
            return cached[1]
        dependents = {}
        for node_id in sorted(self.nodes):
            for work in self.nodes[node_id].get("requires_running") or ():
                dependents.setdefault(work, []).append(node_id)
        self.__dict__["_running_gate_cache"] = (self.nodes, dependents)
        return dependents

    def relied_on_running(self, node_id):
        """Whether some node requires this one running."""
        return node_id in self._running_gate_index()

    def close_lapsed_dependents(self, year):
        """Close every open node whose required work is no longer running, down the chain.
        Returns the ids closed, in the order they closed."""
        projects = self.state.projects
        dependents = self._running_gate_index()
        closed = []
        while True:
            lapsed = sorted(node_id for works in dependents.values() for node_id in works
                            if node_id in projects.operating and self.unmet_running_gates(node_id))
            if not lapsed:
                return closed
            node_id = lapsed[0]
            self.state.household.log.append(
                (year, "%s closed: the work it needs running (%s) has stopped"
                 % (node_id, ", ".join(self.unmet_running_gates(node_id)))))
            self.close_work(node_id, self.CLOSED_GATE_LAPSED, year, cascade=False)
            closed.append(node_id)
