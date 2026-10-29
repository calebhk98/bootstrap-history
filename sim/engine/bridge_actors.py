"""Bridge entries the actors module reads and sends until the owners behind them move into modules.

Each view asks the engine exactly as the old agents port did and is never cached; when its owner moves it publishes the same
name (the owners' catalogue entries in docs/architecture/catalogue say which) and the entry is deleted. The catalogue's names are
coarse, so the entries here are one engine call each. Each command is applied the way the old call did it."""
import contextlib

from sim.assembly.api import QUOTE
from sim.demography.api import rules as demography_rules

from . import view_share
from .bridge import bridge_command, bridge_view

# ---- core: settings and constants the engine declares ----


@bridge_view("shared_answers", kind=QUOTE)
def shared_answers(sim, table):
    """A context in which the answers asked of the engine are shared through `table` (engine/view_share.py)."""
    @contextlib.contextmanager
    def scope():
        opened = view_share.of(sim).open_view_scope(table)
        try:
            yield
        finally:
            view_share.of(sim).close_view_scope(opened)
    return scope()


# ---- production: concerns, their takings and the industry's experience ----


# ---- markets: goods categories, the agent economy's book and the orders the actors place ----


# ---- demography, agriculture, diffusion, mechanics ----


@bridge_view("farm_food_demand_kg")
def farm_food_demand_kg(sim):
    """Kilograms of grain the people would harvest by eating what they need, before the first harvest."""
    technique = sim._farm_technique_this_year
    return (demography_rules.adult_equivalents(sim.view("population")())
            * sim._agriculture.annual_food_demand_kg_per_person(technique.crop))

