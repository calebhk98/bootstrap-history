"""hot_path_caches: the per-year hot paths do not repeat work whose answer cannot have changed.

Complaint 141: a year got slower as more was built because every concern's
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

    def sectors(self):
        # no interest groups: nothing has lost anything in this stub world
        return {}

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


# --- the registry's supply sum.
from sim.engine.actors.registry import ActorRegistry as _Registry
from sim.engine.state import ActorRecord as _Record, ActorsState as _ActorsState


class _TonnesWorld:
    year = 100

    def __init__(self, makers):
        self.makers, self.asked = frozenset(makers), []

    def sectors(self):
        # no interest groups: nothing has lost anything in this stub world
        return {}

    def concerns_making(self, material):
        return self.makers

    def concern_output_tonnes(self, node_id, material, opened_year, staffed):
        self.asked.append(node_id)
        return 0.5

    def market_forget(self, actor_id):
        # the goods market drops an exited actor's standing orders; this stub keeps no book
        pass

    def materials_made_by(self, node_id):
        return ()

    def market_sale(self, actor_id, material, tonnes, from_concerns=None):
        pass


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
# Firms now put their output into the one goods market themselves (`sell_output`); the market's
# total is the flows they report, so there is no registry-wide supply walk left to index.
_tonnes = {actor_id: actor.output_of("steel", _world) for actor_id, actor in _registry.actors.items()}
check("only the actors holding a concern that makes the material report any of it",
      {actor_id for actor_id, tonnes in _tonnes.items() if tonnes > 0.0} == {"firm:017", "firm:042"}
      and abs(sum(_tonnes.values()) - 1.0) < 1e-12, _tonnes)
check("...and an actor with no concern making the material asks the world about none of its concerns",
      _registry.actors["firm:001"].output_of("steel", _world) == 0.0)


# --- the staffing tally survives an actor's turn that left staff as it was found.
_registry = _registry_of_firms(10)
_registry.consider_entry = lambda world: []
for _actor in _registry.actors.values():
    _actor.advance = lambda world: None
_registry.staff_by_trade()
_registry.advance(_TonnesWorld([]))
_tally_after_idle_year = _registry._staff
_registry.staff_by_trade()
_registry.actors["firm:009"].advance = lambda world: _registry.staff_by_trade()
_registry.advance(_TonnesWorld([]))
check("a year in which no actor's staff changed leaves the staffing tally standing after the first turn",
      _tally_after_idle_year is None and _registry._staff is not None)


def _hire(world):
    _registry.actors["firm:003"].workforce["smith"] += 1.0


_registry.actors["firm:003"].advance = _hire
_registry.advance(_TonnesWorld([]))
check("a year in which an actor took people on recounts the staffing",
      _registry.staff_by_trade()["smith"] == 10 * 1.5 + 1.0, _registry._staff)


def _hire_count_and_leave(world):
    _registry.actors["firm:005"].workforce["smith"] += 2.0
    _registry.staff_by_trade()
    _registry.actors["firm:005"].workforce["smith"] -= 2.0


_registry.actors["firm:005"].advance = _hire_count_and_leave
_registry.advance(_TonnesWorld([]))
check("a count taken in the middle of a turn that then undid its hiring is not kept",
      _registry.staff_by_trade()["smith"] == 10 * 1.5 + 2.0, _registry._staff)


# --- reading one trade's staff does not recount every actor's every trade.
class _ItemsCounting(dict):
    walks = 0

    def items(self):
        _ItemsCounting.walks += 1
        return super().items()


_registry = _registry_of_firms(30)
_registry.consider_entry = lambda world: []
for _actor in _registry.actors.values():
    _actor.record.workforce = _ItemsCounting(_actor.record.workforce)
    _actor.advance = lambda world: None
_registry.refresh_staff()
_ItemsCounting.walks = 0
_staffed = [_registry.staff_fte("smith") for _ in range(5)]
check("one trade's staff is read without walking every actor's whole workforce",
      _ItemsCounting.walks == 0 and _staffed[0] == 30 * 1.5 and len(set(_staffed)) == 1,
      (_ItemsCounting.walks, _staffed[0]))
check("...and a trade nobody employs reads as zero", _registry.staff_fte("scribe") == 0.0)
check("...and staff_fte leaves out the asked actor's own people",
      _registry.staff_fte("smith", excluding="firm:004") == 29 * 1.5)


def _hire_and_read(world):
    _registry.actors["firm:004"].workforce["smith"] += 2.0
    _registry.actors["firm:004"].workforce["scribe"] = 0.25
    _registry.staff_fte("smith")


_registry.actors["firm:004"].advance = _hire_and_read
_registry.advance(_TonnesWorld([]))
check("...and the turn of an actor that took on people changes the next count by exactly that",
      _registry.staff_fte("smith") == 30 * 1.5 + 2.0 and _registry.staff_fte("scribe") == 0.25
      and _ItemsCounting.walks == 0, (_registry.staff_fte("smith"), _registry.staff_fte("scribe"), _ItemsCounting.walks))


# --- the kept per-trade sums equal a fresh left-to-right sum after hires, new firms and a year's turns.
import random as _random

_dice = _random.Random(7)
_registry = _registry_of_firms(25)
_registry.consider_entry = lambda world: []
_trades = ["smith", "scribe", "mason"]


def _fresh_sum(trade):
    total = 0.0
    for _identifier in sorted(_registry.actors):
        total += _registry.actors[_identifier].record.workforce.get(trade, 0.0)
    return total


def _random_turn(world):
    _chosen = _random.Random(_dice.random())
    for _ in range(_chosen.randrange(3)):
        _registry._acting.workforce[_chosen.choice(_trades)] = _chosen.random() * 3.7
    _registry.staff_fte(_chosen.choice(_trades))


for _actor in _registry.actors.values():
    _actor.advance = _random_turn
_mismatch = []
for _year in range(6):
    _registry.advance(_TonnesWorld([]))
    for _number in range(3):
        _added = _Record(kind="firm", concerns=set(), workforce={_dice.choice(_trades): _dice.random() * 2.9})
        _new_id = "firm:%03d" % _dice.randrange(1000)
        if _new_id not in _registry.actors:
            _registry.add(_new_id, _added)
            _registry.actors[_new_id].advance = _random_turn
    for _trade in _trades:
        if _registry.staff_fte(_trade) != _fresh_sum(_trade):
            _mismatch.append((_year, _trade))
check("the kept per-trade staff sums equal a fresh sum bit for bit after turns that hired and firms that were added",
      not _mismatch, _mismatch)


# --- counting concerns by category walks the firms once until a concern changes.
_registry = _registry_of_firms(20)
for _identifier, _actor in _registry.actors.items():
    _actor.record.concerns.clear()
    _actor.record.concerns.add("loom")
_loom_nodes = {"loom": {"cat": "cloth"}, "forge": {"cat": "metal"}}
_walked = _count_calls(_registry, "active_firms", lambda: [_registry.concerns_in("cloth", _loom_nodes) for _ in range(50)])
check("concerns of a category are counted from one walk of the firms", _walked == 1, _walked)
check("...and the count is right", _registry.concerns_in("cloth", _loom_nodes) == 20 and _registry.concerns_in("metal", _loom_nodes) == 0)
_registry.actors["firm:003"].record.concerns.add("forge")
check("...and a firm taking on a concern is counted at once",
      _registry.concerns_in("metal", _loom_nodes) == 1 and _registry.concerns_in("cloth", _loom_nodes) == 20)

# --- the material stock moves capacity keys to the pool once, not on every read.
_probe = sim(capital=2000.0)
_ledger = _probe._material_stock()
_ledger["scholar_hours"] += 5.0
_probe._material_stock()
check("a capacity key written to the stock lands in the pool and leaves the stock",
      "scholar_hours" not in _probe._material_stock() and _probe.state.economy.capacity_pool.get("scholar_hours", 0.0) >= 5.0)

# --- mining technology is read once per material until what is built or operating changes.
_probe.mining_tech("iron")
_asked = _count_calls(_probe, "running", lambda: [_probe.mining_tech("iron") for _ in range(20)])
check("mining technology of a material is not recomputed while nothing built or operating changes", _asked == 0, _asked)
