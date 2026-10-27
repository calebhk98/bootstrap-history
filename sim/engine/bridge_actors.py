"""Bridge entries the actors module reads and sends until the owners behind them move into modules.

Each view asks the engine exactly as the old agents port did and is never cached; when its owner moves it publishes the same
name (the owners' catalogue entries in docs/architecture/catalogue say which) and the entry is deleted. The catalogue's names are
coarse, so the entries here are one engine call each. Each command is applied the way the old call did it."""
import contextlib

from sim.agents.api import cast_from_civilisations
from sim.assembly.api import KEYED, QUOTE
from sim.production.api import AccrueExperience

from . import node_upkeep, partner_demand
from .actor_kinds_data import register_mod_actor_kinds
from .bridge import bridge_command, bridge_view
from .data import load_civ
from .foreign_economy_data import not_traded_materials as declared_not_traded_materials
from .industry_depth import RAMP_SHARE_AT_FULL_DEPTH
from .node_revenue_market import basket_market_factor
from .projects_review import SeatReview

# ---- the cast's own data: the kinds mods bring and the roster a game opens with ----


@bridge_view("actor_kinds_registered")
def actor_kinds_registered(sim):
    """Registers the actor kinds mods bring (once per mods directory) before the registry is built."""
    register_mod_actor_kinds()


@bridge_view("opening_cast")
def opening_cast(sim):
    """(home country, entries, profiles): the civilisation played, and every economy trading with it."""
    foreign = [load_civ(civilisation_id) for civilisation_id in sim.partner_countries()]
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
        opened = sim.open_view_scope(table)
        try:
            yield
        finally:
            sim.close_view_scope(opened)
    return scope()


# ---- workforce ----


@bridge_view("concern_staff", kind=KEYED)
def concern_staff(sim, node_id):
    """People of each trade one plant of the concern needs."""
    return sim.concern_staff_by_trade(node_id)


# ---- production: concerns, their takings and the industry's experience ----


@bridge_view("concern_takings", kind=QUOTE)
def concern_takings(sim, node_id, ramp, **options):
    return sim.concern_takings(node_id, ramp, **options)


@bridge_view("concern_gross", kind=QUOTE)
def concern_gross(sim, node_id):
    """Yearly takings of a concern once ramped up, with the market's price for its goods applied."""
    return sim.concern_takings(node_id, 1.0) * sim.node_output_market_factor(sim.nodes[node_id])


@bridge_view("concern_upkeep", kind=QUOTE)
def concern_upkeep(sim, node_id, capacity=1.0, cost_scale=None):
    """Yearly upkeep of a concern at a given capacity, without its crew's pay."""
    node = sim.nodes[node_id]
    return node_upkeep.non_labour_upkeep_money(node["up"], node, capacity, sim.price_index if cost_scale is None else cost_scale)


@bridge_view("node_output_market_factor", kind=QUOTE)
def node_output_market_factor(sim, node):
    return sim.node_output_market_factor(node)


@bridge_view("concern_volume_ratio", kind=QUOTE)
def concern_volume_ratio(sim, node_id):
    return sim.concern_volume_ratio(node_id)


@bridge_view("industry_depth", kind=KEYED)
def industry_depth(sim, node_id):
    return sim.industry_depth(node_id)


@bridge_view("industry_scale_ceiling", kind=KEYED)
def industry_scale_ceiling(sim, node_id):
    return sim.industry_scale_ceiling(node_id)


@bridge_view("ramp_share_at_full_depth")
def ramp_share_at_full_depth(sim):
    return RAMP_SHARE_AT_FULL_DEPTH


@bridge_view("basket_market_factor", kind=QUOTE)
def basket_market_factor_view(sim, sold, bought, long_run_prices, price_now):
    return basket_market_factor(sold, bought, long_run_prices, price_now)


@bridge_view("seat_review", kind=QUOTE)
def seat_review(sim, world, year):
    """The founder's seat's answers to a business review (engine/projects_review.py)."""
    return SeatReview(world, year, sim)


@bridge_command(AccrueExperience)
def accrue_experience(sim, command):
    sim.accrue_industry_experience()


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
    return (sim._adult_equivalent_population(sim.population)
            * sim._agriculture.annual_food_demand_kg_per_person(technique.crop))


@bridge_view("state_military_diffusion")
def state_military_diffusion(sim):
    return sim.state_military_diffusion()


@bridge_view("nodes_with_mechanic", kind=QUOTE)
def nodes_with_mechanic(sim, mechanic):
    return sim.nodes_with_mechanic(mechanic)


# ---- foreign trade ----


@bridge_view("not_traded_materials")
def not_traded_materials(sim):
    return declared_not_traded_materials()


@bridge_view("home_household_tonnes", kind=QUOTE)
def home_household_tonnes(sim, prices_in_hours):
    """{material: tonnes a year} the home households buy at these prices (labour hours a unit), scaled to the opening's people."""
    return partner_demand.budget_scaled_final_tonnes(prices_in_hours, sim._opening_population())
