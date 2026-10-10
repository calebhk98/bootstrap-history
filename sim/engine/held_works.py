"""What an actor holds that is also in service: the one answer geography, freight and labour read.

A node done is held; a venture that is shut is not (`running`); an action's declared results
(sim/engine/action_results.py) stand while the action is held. Every reader of "which technologies do
these people hold" calls `held_and_running` rather than building a set from `done`.
"""
from . import action_results


class HeldWorksMixin:

    def held_and_running(self, include_starting=True):
        """The ids and result tokens held now: completed and granted nodes that are in service, the
        civilisation's starting ones when `include_starting`, and what the held actions return."""
        projects = self.state.projects
        key = (self.household.done_version, self.household.operating_version, id(self.nodes),
               self.built_ways_stamp())
        cache = self.__dict__.setdefault("_held_running_cache", {})
        cached = cache.get(include_starting)
        if cached is not None and cached[0] == key:
            return cached[1]
        held = set(projects.done) | set(projects.granted)
        held = {node_id for node_id in held
                if node_id in projects.granted or node_id not in self.nodes or self.running(node_id)}
        if include_starting:
            held |= set(self.civ.get("starting_techs") or ())
        held = action_results.expand(self.nodes, held)  # a frozenset
        cache[include_starting] = (key, held)
        return held

    def built_ways_stamp(self):
        """A stamp of the ways built, since a node may require length of road or track to be running."""
        return sum(len(ways) for ways in self.state.economy.improvements.values())

    def partner_gate_refusal(self, civilization_id):
        """Why trade with a partner some action returns cannot begin yet, else None. A partner no action
        returns is open from the start."""
        if civilization_id not in action_results.partner_ids(self.nodes):
            return None
        if action_results.token("partner", civilization_id) in self.held_and_running():
            return None
        return "you have not yet reached %s" % civilization_id
