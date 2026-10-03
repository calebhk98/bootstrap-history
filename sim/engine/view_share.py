"""Answers shared by everything one view of the world asks in a turn.

An actor's turn prices the same projects and the same trades once per firm,
though the answer is a fact about the world, not about the actor asking. A
view that asks many questions (`SimWorld`) opens a scope here, and an answer
is computed once while everything it read is unchanged. A hit is confirmed by
identity on the objects the world rebuilds when it changes (the price table,
the year's demand, the actors' demand tally) and by value on the counters and
the entry's own inputs. Outside a view nothing is shared.
"""


class ViewShareMixin:
    _view_scope = None

    def open_view_scope(self, scope):
        """Share answers through `scope` (a dict the view owns); returns what to hand back to
        `close_view_scope`."""
        opened, self._view_scope = self._view_scope, scope
        return opened

    def close_view_scope(self, opened):
        self._view_scope = opened

    def _view_world_stamp(self):
        """(objects compared by identity, values compared by equality) for what every shared
        answer reads beyond its own inputs; None when the world has no demand table to compare."""
        demand = getattr(self.household, "_material_demand_cache", None)
        if demand is None:
            return None
        registry = self.actors
        economy = self.state.economy
        projects = self.state.projects
        return ((self._material_prices(), demand),
                (self.goods_market.others_stamp(), registry.version[0], len(registry.actors), self.state.scenario.year,
                 self.household.done_version, self.household.operating_version,
                 len(projects.done), len(projects.operating),
                 economy.forest_ha, economy.nitre_bed_m2, self.population.total,
                 economy.output_per_head, len(economy.mines)))

    def _shared_answer(self, key, inputs, compute):
        """`compute()` reused while the world stamp holds and `inputs` (what the answer reads that
        the stamp does not) are equal to those it was computed with."""
        scope = self._view_scope
        if scope is None:
            return compute()
        stamp = self._view_world_stamp()
        if stamp is None:
            return compute()
        objects, values = stamp
        held = scope.get("world")
        if (held is None or held[1] != values
                or any(kept is not now for kept, now in zip(held[0], objects))):
            scope["world"] = (objects, values)
            scope["answers"] = {}
        answers = scope["answers"]
        entry = answers.get(key)
        if entry is not None and entry[0] == inputs:
            return entry[1]
        answer = compute()
        answers[key] = (inputs, answer)
        return answer

    def _shared_bill(self, node_id, compute):
        """The node's material bill, reused while the world stamp and the node's stock hold."""
        if self._view_scope is None:
            return compute()
        keys = self._shared_bill_keys(node_id)
        return self._shared_answer(("bill", node_id), tuple(self.material_stock_t(key) for key in keys), compute)

    def _shared_bill_keys(self, node_id):
        """The commodities a node's bill draws on; these change only with the done set."""
        return self._done_memo("bill_keys", node_id, lambda: tuple(sorted({
            self._material_tag(material)[0] for material in self.project_material_needs(node_id)})))
