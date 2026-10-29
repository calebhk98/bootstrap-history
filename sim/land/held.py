"""What an actor holds that is also in service: the one answer geography, freight and labour read.

A node done is held; a venture that is shut is not (`running`); an action's declared results (action_results.py) stand while the
action is held. Every reader of "which technologies do these people hold" asks `held_techniques` rather than building a set from
`done`.
"""
from typing import Any, Optional

from sim.refusal import Refusal

from . import action_results


class Held:
    """Mixed into `Land`."""

    needs: Any
    _caches: dict

    def held_techniques(self, include_starting: bool = True) -> frozenset:
        """The ids and result tokens held now: completed and granted nodes that are in service, the civilisation's starting ones
        when `include_starting`, and what the held actions return."""
        needs = self.needs
        done_version, operating_version = needs.held_and_running_versions()
        key = (done_version, operating_version, self.built_ways_stamp())
        nodes = needs.tree_nodes()
        cache = self._caches.setdefault("held_and_running", {})
        cached = cache.get(include_starting)
        if cached is not None and cached[0] == key and cached[2] is nodes:
            return cached[1]
        granted = needs.techniques_granted()
        held = set(needs.techniques_held()) | set(granted)
        held = {node_id for node_id in held if node_id in granted or node_id not in nodes or needs.running[node_id]}
        if include_starting:
            held |= set(needs.civilisation().get("starting_techs") or ())
        held = action_results.expand(nodes, held)
        cache[include_starting] = (key, held, nodes)
        return held

    def built_ways_stamp(self) -> int:
        """A stamp of the ways built, since a node may require length of road or track to be running."""
        return sum(len(ways) for ways in self.world.improvements.values())

    def partner_gate_refusal(self, civilization_id: str) -> Optional[Refusal]:
        """Why trade with a partner some action returns cannot begin yet, else None. A partner no action returns is open from the
        start."""
        if civilization_id not in action_results.partner_ids(self.needs.tree_nodes()):
            return None
        if action_results.token("partner", civilization_id) in self.held_techniques():
            return None
        return Refusal("partner_not_reached", "you have not yet reached %s" % civilization_id)
