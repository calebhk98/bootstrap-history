"""Derived node figures follow the techniques held now and the civilisation playing (Complaints/310, 317): the gate set a held set of
techniques reduces to, the derivation cached per civilisation and gate set and tagged with its civilisation, and the re-derivation a
game makes when its society's gate set changes. The solver, the energy prices and the node arithmetic are replaced by recorders so
only the caching and wiring are called."""
from types import SimpleNamespace
from unittest import mock

from sim.prices import prices as price_solver, solve_prices

from sim.engine import node_rederive, node_revenue
from sim.engine.node_rederive import NodeRederiveMixin, held_gate_set

from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

GATE, OTHER_GATE = "gate_a", "gate_b"

# --- the gate set a held set of techniques reduces to.
with mock.patch.object(price_solver, "all_gate_nodes", return_value={GATE, OTHER_GATE}):
    check("the gate set is the held techniques that gate production", held_gate_set({GATE, "plain_tech"}) == frozenset({GATE}))
    check("a technique that gates nothing leaves the gate set as it was", held_gate_set({GATE, "plain_tech", "another"}) == held_gate_set({GATE}))
    check("a gate the society learns enters the gate set", OTHER_GATE in held_gate_set({GATE, OTHER_GATE}) and OTHER_GATE not in held_gate_set({GATE}))
    check("holding nothing gives an empty gate set", held_gate_set(()) == frozenset())


# --- for_civilisation derives once per civilisation and gate set, and tags what it returns.
class _Schedule:
    money_per_labour_hour = 2.0

    def document(self):
        return {"money_per_labour_hour": 2.0}

    def wages_per_hour(self):
        return {"labourer": 1.0}


def _derive(civ, nodes, held=None):
    return node_revenue.for_civilisation(nodes, civ, _Schedule(), held_techs=held)


def _stamp(copies, goods, wages, rate, energy):
    for node in copies:
        node["rev_hours"] = 7.0 + len(goods)


CIV = {"id": "testland", "starting_techs": ["start_tech"], "starting_interest_rate": 0.05}
NODES = {"mill": {"id": "mill", "kind": "X", "sch": 0, "art": 0, "lab": {}, "name": "Mill", "rev_hours": 99.0},
         "idea": {"id": "idea", "kind": "SCIENCE", "sch": 0, "art": 0, "lab": {}, "name": "Idea"}}
with mock.patch.dict(node_revenue._DERIVED_FOR_CIVILISATION, clear=True), \
        mock.patch.object(node_revenue, "derivation_calls", []) as calls, \
        mock.patch.object(price_solver, "all_gate_nodes", return_value={GATE, OTHER_GATE}), \
        mock.patch.object(price_solver, "territory_fingerprint", return_value="land"), \
        mock.patch.object(solve_prices, "wage_ratios_by_trade", return_value={"labourer": 1.0}), \
        mock.patch.object(price_solver, "priced_goods_table", return_value=({"grain": 1.0}, {})) as priced, \
        mock.patch.object(node_revenue.energy_prices, "graded", return_value=None), \
        mock.patch.object(node_revenue, "apply_revenue", side_effect=_stamp):
    first = _derive(CIV, NODES)
    after_first = len(calls)
    _derive(CIV, NODES)
    check("a second derivation of the same civilisation and gate set is a cache hit", after_first == 1 and len(calls) == 1, len(calls))
    _derive(CIV, NODES, held=["start_tech", "plain_tech"])
    check("a technique that gates nothing does not change the cache key", len(calls) == 1, len(calls))
    _derive(CIV, NODES, held=["start_tech", GATE])
    check("a new gate set derives once", len(calls) == 2, len(calls))
    _derive(CIV, NODES, held=["start_tech", GATE])
    check("...and not again", len(calls) == 2, len(calls))
    _derive(dict(CIV, id="otherland"), NODES)
    check("another civilisation derives its own figures", len(calls) == 3, len(calls))
    default = priced.call_args_list[0].args[0]
    check("with no held set given the civilisation's starting techniques are the held set", default == ["start_tech"], default)
    check("a derived figure is the civilisation's: each node carries the civilisation it was derived for",
          {node["_derived_for"] for node in first.values()} == {"testland"}, first)
    check("a node the derivation gives a figure takes it; the caller's tree is untouched",
          first["mill"]["rev_hours"] == 8.0 and NODES["mill"]["rev_hours"] == 99.0, (first["mill"], NODES["mill"]))

# --- a game re-derives when the gate set its society holds changes, and only then.
def _game(derived_gates, held):
    log = []
    game = SimpleNamespace(
        _derived_gate_set=derived_gates, _society_held_techs=lambda: held, start_civ={"id": "testland"}, nodes={"old": {}},
        state=SimpleNamespace(economy=SimpleNamespace(nodes_money_per_labour_hour=None)),
        _done_changed=lambda: log.append("done"), _operating_changed=lambda: log.append("operating"), log=log)
    return game


schedule = _Schedule()
with mock.patch.object(node_rederive, "build_schedule", return_value=schedule), \
        mock.patch.object(node_rederive.node_revenue, "for_civilisation", return_value={"n": {}}) as derive, \
        mock.patch.object(node_rederive.money_units, "price_nodes") as price, \
        mock.patch.object(node_rederive.opening_money, "priced_nodes", return_value={"new": {}}), \
        mock.patch.object(price_solver, "all_gate_nodes", return_value={GATE}):
    unchanged = _game(frozenset({GATE}), {GATE, "plain_tech"})
    NodeRederiveMixin.refresh_derived_nodes(unchanged)
    check("a society whose gate set has not changed is not re-derived", not derive.called and unchanged.nodes == {"old": {}} and unchanged.log == [])
    learned = _game(frozenset(), {GATE})
    NodeRederiveMixin.refresh_derived_nodes(learned)
    check("a society that has learned a gate is re-derived at the techniques it holds",
          derive.call_args.kwargs["held_techs"] == {GATE} and learned.nodes == {"new": {}} and learned._derived_gate_set == frozenset({GATE}), derive.call_args)
    check("the new figures are priced in the schedule's coin and the memos told", price.call_args.args[1:] == (schedule.wages_per_hour(), 2.0)
          and learned.state.economy.nodes_money_per_labour_hour == 2.0 and learned.log == ["done", "operating"], learned.log)
