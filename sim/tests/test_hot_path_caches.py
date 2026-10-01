"""hot_path_caches: the per-year hot paths do not repeat work whose answer cannot have changed.

Complaint 145: a year got slower as more was built because every concern's
output looked up the production catalog through a path-resolving call.
"""
import os

from .harness import *  # noqa: F401,F403


def _count_calls(function_owner, name, work):
    """How many times `work()` calls `function_owner.name`."""
    original = getattr(function_owner, name)
    calls = []

    def counting(*args, **kwargs):
        calls.append(1)
        return original(*args, **kwargs)
    setattr(function_owner, name, counting)
    try:
        work()
    finally:
        setattr(function_owner, name, original)
    return len(calls)


def _look_up_output_many_times():
    from sim.engine.actors.supply import materials_made_by
    for _ in range(500):
        materials_made_by("iron_smelting")


from sim.engine.actors.supply import materials_made_by as _warm
_warm("iron_smelting")
check("a warm production lookup resolves no filesystem paths",
      _count_calls(os.path, "abspath", _look_up_output_many_times) == 0)
check("a warm production lookup lists no directories",
      _count_calls(os, "listdir", _look_up_output_many_times) == 0)

# A year's wall-clock budget is generous on purpose: it catches a return of the
# per-call catalog scan (tens of times slower), not machine noise.
_budget_sim = sim(capital=200000.0)
_start = time.process_time()
for _ in range(3):
    _budget_sim.step()
_elapsed = time.process_time() - _start
check("three early years of the default run take well under a minute of CPU",
      _elapsed < 60.0, "%.1fs" % _elapsed)


# --- an actor's supply of a material looks only at the concerns that make it.
from sim.engine.actors.base import Actor as _Actor


class _CountingWorld:
    year = 100

    def __init__(self, makers):
        self.makers, self.asked = frozenset(makers), []

    def concerns_making(self, material):
        return self.makers

    def concern_output_tonnes(self, node_id, material, opened_year, staffed):
        self.asked.append(node_id)
        return 2.0


class _ManyConcerns(_Actor):
    concerns = ["node_%02d" % number for number in range(40)]


_world = _CountingWorld(["node_07", "node_03"])
_total = _ManyConcerns().output_of("steel", _world)
check("an actor's supply asks only the concerns that make the material, in id order",
      _world.asked == ["node_03", "node_07"] and _total == 4.0, _world.asked)
_world = _CountingWorld([])
_ManyConcerns().output_of("steel", _world)
check("an actor with no concern making the material asks about none",
      _world.asked == [], _world.asked)


# --- the registry's supply sum and staffing tally.
from sim.engine.actors.registry import ActorRegistry as _Registry
from sim.engine.state import ActorRecord as _Record, ActorsState as _ActorsState


class _TonnesWorld:
    year = 100

    def __init__(self, makers):
        self.makers, self.asked = frozenset(makers), []

    def concerns_making(self, material):
        return self.makers

    def concern_output_tonnes(self, node_id, material, opened_year, staffed):
        self.asked.append(node_id)
        return 0.5


def _registry_of_firms(count):
    state = _ActorsState()
    for number in range(count):
        state.records["firm:%03d" % number] = _Record(
            kind="firm", concerns={"plain_%03d" % number},
            workforce={"smith": 1.5})
    registry = _Registry(state)
    for number in [n for n in (17, 42) if n < count]:
        registry.actors["firm:%03d" % number].concerns.add("steelworks")
    return registry


_registry = _registry_of_firms(60)
_world = _TonnesWorld(["steelworks"])
_actors_asked = []
_original_output_of = _Actor.output_of


def _counting_output_of(self, material, world):
    _actors_asked.append(self.actor_id)
    return _original_output_of(self, material, world)


_Actor.output_of = _counting_output_of
try:
    _total = _registry.supply("steel", _world)
finally:
    _Actor.output_of = _original_output_of
check("registry supply asks only the actors that hold a concern making the material",
      _actors_asked == ["firm:017", "firm:042"] and abs(_total - 1.0) < 1e-12,
      (_actors_asked, _total))
_registry.actors["firm:042"].record.exited_year = 90
_world = _TonnesWorld(["steelworks"])
check("...and an exited firm no longer supplies",
      abs(_registry.supply("steel", _world) - 0.5) < 1e-12)

_registry = _registry_of_firms(10)
_registry.consider_entry = lambda world: []
for _actor in _registry.actors.values():
    _actor.advance = lambda world: None
_registry.staff_by_trade()
_registry.advance(_TonnesWorld([]))
check("a year in which no actor's staff changed keeps the staffing tally",
      _registry._staff is not None)


def _hire(world):
    _registry.actors["firm:003"].workforce["smith"] += 1.0


_registry.actors["firm:003"].advance = _hire
_registry.advance(_TonnesWorld([]))
check("a year in which an actor took people on recounts the staffing",
      _registry._staff is None or _registry._staff["smith"] == 10 * 1.5 + 1.0,
      _registry._staff)
