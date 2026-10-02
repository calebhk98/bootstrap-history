"""What a forgotten technology still has going for it when it is rebuilt.

A node lost to a sack is not the same as a node never built: a dispersed copy
of the record, people who still practise its trades, and plant built on it all
survive. This module turns those three facts into the share of the original
work a rebuild does not have to redo. Everything is read from current state;
the only constant is the ceiling on how much of a lost node can ever survive.
"""
from sim.constants import declare


class RebuildMixin:
    REBUILD_RETAINED_CEILING = declare(
        "REBUILD_RETAINED_CEILING", 0.75, kind="temporary_heuristic",
        unit="fraction of a node's work, money and calendar", source=None,
        confidence="D",
        why="The most of a forgotten node a rebuild can ever skip however "
            "much survives: even with a copy, practitioners and plant, the "
            "knowledge has to be re-established in the society. Tuned "
            "ceiling; the share below it is derived from state.")

    def _dependents_index(self):
        """{node id: ids of nodes listing it as a prerequisite}, built once per tree."""
        cached = self.__dict__.get("_dependents_index_cache")
        if cached is not None and cached[0] is self.nodes:
            return cached[1]
        index = {}
        for node_id, node in self.nodes.items():
            for prerequisite in node["pre"]:
                index.setdefault(prerequisite, []).append(node_id)
        self.__dict__["_dependents_index_cache"] = (self.nodes, index)
        return index

    def is_being_rebuilt(self, node_id):
        """Whether `node_id` was built once, was lost, and is not held now."""
        projects = self.state.projects
        return node_id in (projects.forgotten or {}) and node_id not in projects.done

    def rebuild_survivals(self, node_id):
        """{what survives: share 0..1} for a forgotten node, from current state:
        `copy` the record held beyond one site, `practice` the share of its
        trades still worked by people you keep, `plant` the share of what was
        built on it that still stands."""
        node = self.nodes[node_id]
        none_chance = self.CORPUS_HEDGE_LOSS_CHANCE_NONE
        chance, _fraction, _hedge = self.corpus_hedge()
        copy = max(0.0, (none_chance - chance) / none_chance) if none_chance > 0 else 0.0
        employees = self.state.household.employees
        trades = list(node["lab"])
        practice = (sum(1 for trade in trades if employees.get(trade, 0.0) >= 1.0) / len(trades)
                    if trades else 0.0)
        dependents = self._dependents_index().get(node_id, [])
        done = self.state.projects.done
        plant = (sum(1 for dependent in dependents if dependent in done) / len(dependents)
                 if dependents else 0.0)
        return {"copy": copy, "practice": practice, "plant": plant}

    def rebuild_retained_share(self, node_id):
        """The share of the original work a rebuild skips; zero for a node that was never lost."""
        if not self.is_being_rebuilt(node_id):
            return 0.0
        missing = 1.0
        for share in self.rebuild_survivals(node_id).values():
            missing *= 1.0 - share
        return self.REBUILD_RETAINED_CEILING * (1.0 - missing)

    def rebuild_work_factor(self, node_id):
        """What is left to do, as a fraction of a first build: frozen at the
        start of a running project, live before it."""
        record = self.state.projects.active.get(node_id)
        if record is not None and "rebuild_factor" in record:
            return record["rebuild_factor"]
        return 1.0 - self.rebuild_retained_share(node_id)

    def rebuild_explanation(self, node_id):
        """One line for `why` on a lost node: what a rebuild keeps and why, or None."""
        if not self.is_being_rebuilt(node_id):
            return None
        survivals = self.rebuild_survivals(node_id)
        words = {"copy": "a copy of the record survives",
                 "practice": "people who practise its trades are still on your books",
                 "plant": "plant built on it still stands"}
        kept = [words[kind] for kind, share in survivals.items() if share > 0]
        retained = self.rebuild_retained_share(node_id)
        return ("forgotten in %d. A rebuild redoes %d%% of the original work, money and "
                "calendar (%d%% is saved) because %s."
                % (self.state.projects.forgotten[node_id],
                   round((1.0 - retained) * 100), round(retained * 100),
                   " and ".join(kept) if kept else
                   "nothing of it survives: no copy, no practitioners, no plant, "
                   "so it costs what a first build does"))
