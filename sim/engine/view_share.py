"""Answers shared by everything one view of the world asks in a turn.

An actor's turn prices the same projects and the same trades once per firm,
though the answer is a fact about the world, not about the actor asking. A
view that asks many questions (`ActorWorld`) opens a scope here, and an answer
is computed once while everything it read is unchanged. A hit is confirmed by
identity on the objects the world rebuilds when it changes (the price table,
the year's demand, the actors' demand tally) and by value on the counters and
the entry's own inputs. Outside a view nothing is shared.

This is composition code, not a module: the stamp that confirms a hit names what eight owners' changes make stale (prices, the
year's demand, the techniques in force, forest, nitre, mines, people), and only the root knows them all. One service per game,
reached by `of(sim)`; the actors, workforce and materials bridges are its callers.
"""


def of(sim):
    """The game's shared-answer service, made on first use."""
    held = sim.__dict__.get("_view_share")
    if held is None:
        held = sim._view_share = ViewShare(sim)
    return held


class ViewShare:
    _view_scope = None

    def __init__(self, sim):
        self.sim = sim
        self._standalone_scope = {}

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
        sim = self.sim
        demand = sim.view("material_demand_held")()
        if demand is None:
            return None
        projects = sim.state.projects
        return ((sim._material_prices(), demand),
                (sim.goods_market.others_stamp(), sim.state.scenario.year,
                 sim.household.done_version, sim.household.operating_version,
                 len(projects.done), len(projects.operating),
                 sim.view("forest_hectares")(), sim.view("nitre_beds")()["square_metres"], sim.view("population")().total,
                 sim.real_output_per_head(), len(sim.view("mine_workings")())))

    def _standalone_stamp(self):
        """The world stamp of an answer shared outside a view: what changes the people, the techniques in
        force and the year (it leaves out the prices and the year's trade, which such an answer does not read)."""
        sim = self.sim
        projects = sim.state.projects
        return ((), (sim.state.scenario.year, sim.household.done_version, sim.household.operating_version,
                     len(projects.done), len(projects.operating), sim.view("forest_hectares")(),
                     sim.view("nitre_beds")()["square_metres"], sim.view("population")().total, sim.real_output_per_head(),
                     len(sim.view("mine_workings")())))

    def _shared_answer(self, key, inputs, compute, standalone=False):
        """`compute()` reused while the world stamp holds and `inputs` (what the answer reads that
        the stamp does not) are equal to those it was computed with. An answer that is `standalone`
        is shared outside a view too, through one table the world keeps."""
        scope = self._view_scope
        if scope is None:
            if not standalone:
                return compute()
            scope = self._standalone_scope
            stamp = self._standalone_stamp()
        else:
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
        return self._shared_answer(("bill", node_id), tuple(self.sim.material_stock_t(key) for key in keys), compute)

    def _shared_bill_keys(self, node_id):
        """The commodities a node's bill draws on; these change only with the done set."""
        sim = self.sim
        return sim._done_memo("bill_keys", node_id, lambda: tuple(sorted({
            sim._material_tag(material)[0] for material in sim.project_material_needs(node_id)})))
