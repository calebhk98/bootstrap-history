"""Toy modules for the assembly framework tests: a base owner with every view kind, and a reader above it."""
import dataclasses

from sim.assembly.api import (KEYED, QUOTE, Command, Module, ModuleSpec, ViewSpec, assemble)


@dataclasses.dataclass(frozen=True)
class SetValue(Command):
    value: int


@dataclasses.dataclass(frozen=True)
class Unapplied(Command):
    pass


class Base(Module):
    """Owner of `value`; every compute method appends to `calls` so a test can count recomputations."""

    def setup(self):
        self.value = 1
        self.calls = []
        self.per_seat = {}
        self.side_value = 100

    def side(self):
        return self.side_value

    def raw(self):
        self.calls.append("raw")
        return self.value

    def double(self):
        self.calls.append("double")
        return self.value * 2

    def mine(self):
        self.calls.append("mine")
        return self.per_seat.get(self.clock.acting_seat, 0)

    def keyed(self, key):
        self.calls.append(("keyed", key))
        return self.value * key

    def quote(self, extra):
        self.calls.append("quote")
        return self.value + extra

    def uncached(self):
        self.calls.append("uncached")
        return self.value

    def apply_set(self, command):
        self.value = command.value
        self.bump("data")
        return command.value

    def run_market(self):
        return "market"


class Top(Module):
    def setup(self):
        self.calls = []

    def derived(self):
        self.calls.append("derived")
        return self.needs.double() + 1


BASE_VIEWS = (
    ViewSpec("raw", "raw", channels=("data",)),
    ViewSpec("double", "double", channels=("data",)),
    ViewSpec("side", "side", channels=("other",)),
    ViewSpec("mine", "mine", channels=("mine",), seat_scoped=True),
    ViewSpec("keyed", "keyed", kind=KEYED, channels=("data",)),
    ViewSpec("quote", "quote", kind=QUOTE, channels=("data",)),
    ViewSpec("uncached", "uncached", cached=False))

BASE = ModuleSpec("base", Base, channels=("data", "other", "mine"), publishes=BASE_VIEWS,
                  applies=((SetValue, "apply_set"),))
TOP = ModuleSpec("top", Top, publishes=(ViewSpec("derived", "derived", inputs=("double",)),), reads=("double",))


def changed(spec, **fields):
    return dataclasses.replace(spec, **fields)


def build(*extra, operations=(), shipped=None, **options):
    """Assemble BASE and TOP (or `shipped`) plus any extra shipped specs."""
    return assemble(list(shipped if shipped is not None else (BASE, TOP)) + list(extra), operations, **options)
