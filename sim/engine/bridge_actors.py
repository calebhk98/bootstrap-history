"""Bridge entries the actors module reads and sends until the owners behind them move into modules.

Each view asks the engine exactly as the old agents port did and is never cached; when its owner moves it publishes the same
name (the owners' catalogue entries in docs/architecture/catalogue say which) and the entry is deleted. The catalogue's names are
coarse, so the entries here are one engine call each. Each command is applied the way the old call did it."""
import contextlib

from sim.agents.api import cast_from_civilisations
from sim.assembly.api import KEYED, QUOTE
from sim.demography.api import rules as demography_rules

from . import bridge_land, view_share
from .actor_kinds_data import declared_kinds
from .bridge import bridge_command, bridge_view
from .data import load_civ
from .foreign_economy_data import not_traded_materials as declared_not_traded_materials

# ---- the cast's own data: the kinds mods declare and the roster a game opens with ----


@bridge_view("declared_actor_kinds")
def declared_actor_kinds(sim):
    """{kind id: class} for the actor kinds the installed mods declare in data."""
    return declared_kinds(bridge_land.MODS_DIR)



@bridge_view("opening_cast")
def opening_cast(sim):
    """(home country, entries, profiles): the civilisation played, and every economy trading with it."""
    foreign = [load_civ(civilisation_id) for civilisation_id in sim.view("partners")()]
    return cast_from_civilisations(sim.start_civ, foreign)


# ---- core: settings and constants the engine declares ----


@bridge_view("game_setting", kind=KEYED)
def game_setting(sim, name):
    return sim.cfg[name]


@bridge_view("legacy_constant", kind=KEYED)
def legacy_constant(sim, name):
    """A number `Sim` still declares (the goods categories, the state's funding terms, the population scale), read as the game has it."""
    return getattr(sim, name)


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


@bridge_view("materials_serving", kind=KEYED)
def materials_serving(sim, need_id):
    from . import need_substitutes
    return need_substitutes.serving(need_id)


# ---- demography, agriculture, diffusion, mechanics ----


@bridge_view("nutrition_ratio_last_year")
def nutrition_ratio_last_year(sim):
    """The share of the people's food need the last year's supply met, or None before a year has been stepped."""
    flows = getattr(sim, "_last_demographic_step", None)
    return None if flows is None else float(flows.nutrition_ratio)


@bridge_view("farm_food_demand_kg")
def farm_food_demand_kg(sim):
    """Kilograms of grain the people would harvest by eating what they need, before the first harvest."""
    technique = sim._farm_technique_this_year
    return (demography_rules.adult_equivalents(sim.view("population")())
            * sim._agriculture.annual_food_demand_kg_per_person(technique.crop))


@bridge_view("state_military_diffusion")
def state_military_diffusion(sim):
    return sim.view("diffusion_index")["military"]


@bridge_view("nodes_with_mechanic", kind=QUOTE)
def nodes_with_mechanic(sim, mechanic):
    return tuple(sim.view("mechanic")[mechanic])


# ---- foreign trade ----


@bridge_view("not_traded_materials")
def not_traded_materials(sim):
    return declared_not_traded_materials()
