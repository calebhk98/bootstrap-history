"""The shipped workforce module assembled with one stand-in module that publishes every view it reads (with the owner's kind)
and applies every command it sends, so a test writes through the module's own commands and reads its own cached views."""
import dataclasses

from sim.assembly.api import KEYED, QUOTE, Module, ModuleSpec, ViewSpec, assemble
from sim.engine.game_assembly import shipped_specs
from sim.workforce.module_spec import MODULE_SPECS as WORKFORCE_SPECS
from sim.workforce.state import WorkforceSeat, WorkforceSociety

STAND_IN = "stand_in"


def _kinds_of_readable_views():
    kinds = {}
    for spec in shipped_specs():
        if spec.module_id != "workforce":
            kinds.update({view.name: view.kind for view in spec.publishes})
    return kinds


def stand_in_spec(workforce_spec, answers):
    """A module publishing every non-workforce view the workforce reads; `answers` maps a view name to its value, a function of no
    arguments for a table, of the key for a keyed view, of its arguments for a quote."""
    kinds = _kinds_of_readable_views()
    own = {view.name for view in workforce_spec.publishes} | {point.name for point in workforce_spec.extension_points}
    names = sorted(name for name in workforce_spec.reads if name not in own)
    methods = {}
    for name in names:
        methods[name] = lambda self, *arguments, _name=name: self.answers[_name](*arguments)
    applied = {command for command, _handler in workforce_spec.applies}
    sent = [command for command in workforce_spec.sends if command not in applied]
    commands = {"apply_%d" % index: (lambda self, command: None) for index in range(len(sent))}
    holder = type("StandIn", (Module,), {**methods, **commands, "answers": answers})
    return ModuleSpec(STAND_IN, holder, publishes=tuple(ViewSpec(name, name, kind=kinds[name], cached=False) for name in names),
                      applies=tuple((command, "apply_%d" % index) for index, command in enumerate(sent)))


def build(answers=None, operations=(), workforce_spec=None, **options):
    """(assembly, workforce module) with the stand-in answering `answers` (a view not named answers with None)."""
    spec = workforce_spec or WORKFORCE_SPECS[0]
    given = dict(answers or {})
    every = {name: (lambda *arguments, _name=name: given.get(_name)) for name in spec.reads}
    stand_in = stand_in_spec(spec, {**every, **{name: _as_function(value) for name, value in given.items()}})
    assembly = assemble([spec, stand_in], list(operations), **options)
    workforce = assembly.modules["workforce"]
    workforce.world, workforce.seat = WorkforceSociety(), WorkforceSeat()
    return assembly, workforce


def _as_function(value):
    return value if callable(value) else (lambda *arguments, _value=value: _value)


def changed(spec, **fields):
    return dataclasses.replace(spec, **fields)
