"""The scenario module over a plain world state, for tests whose host is a stand-in: the host reads `view(name)` and sends
commands as a game does, and the module's own handlers apply them. `module(...)` is the module; `host(...)` a namespace
with `view`, `send`, `rng` and the module as `_scenario`, plus any attributes given."""
import random
from types import SimpleNamespace

from sim.scenario.module import Scenario
from sim.scenario.module_spec import MODULE_SPECS
from sim.scenario.state import ScenarioWorld
from sim.tests import module_harness

WORLD_FIELDS = ("year", "fog", "fuzzy_estimates", "fuzzy_salt")


def module(**world_fields):
    return module_harness.build(Scenario, world=ScenarioWorld(**world_fields), module_id="scenario")


def host(seed=1, **attributes):
    """A game stand-in: the year, the fog and the fuzzy-estimates option are the module's; `attributes` are added as given."""
    scenario = module(**{name: attributes.pop(name) for name in WORLD_FIELDS if name in attributes})
    views = {spec.name: getattr(scenario, spec.compute) for spec in MODULE_SPECS[0].publishes}
    handlers = {command: getattr(scenario, method) for command, method in MODULE_SPECS[0].applies}
    return SimpleNamespace(_scenario=scenario, rng=random.Random(seed), view=lambda name: views[name],
                           send=lambda command: handlers[type(command)](command), **attributes)
