"""Bridge entries the actors module reads and sends until the owners behind them move into modules.

Each view asks the engine exactly as the old agents port did and is never cached; when its owner moves it publishes the same
name (the owners' catalogue entries in docs/architecture/catalogue say which) and the entry is deleted. The catalogue's names are
coarse, so the entries here are one engine call each. Each command is applied the way the old call did it."""
import contextlib

from sim.agents.api import cast_from_civilisations
from sim.assembly.api import KEYED, QUOTE
from sim.finance.api import DefaultOnDebt, RefreshLenderOffers
from sim.markets.api import ForgetActorOrders, NoteActorPurchase, NoteActorSale
from sim.production.api import AccrueExperience
from sim.workforce.api import ReleaseStaff

from . import market_demand, partner_demand, trade_duty
from .actor_kinds_data import register_mod_actor_kinds
from .bridge import bridge_command, bridge_view
from .data import TRADES_ABSENT, load_civ
from .economy_debt_service import DebtServiceMixin
from .economy_port_setup import unit_mass_kg
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


@bridge_view("labour_market")
def labour_market(sim):
    """The one labour market every employer asks: quote, hire, release, read the pressure (the object itself)."""
    return sim.economy.labour


@bridge_view("available_trades")
def available_trades(sim):
    return sim.labour.available_trades()


@bridge_view("is_craft_trade", kind=KEYED)
def is_craft_trade(sim, trade):
    return sim.labour.is_craft_trade(trade)


@bridge_view("taught_trade_people", kind=KEYED)
def taught_trade_people(sim, trade):
    return sim.labour.taught_trade_people(trade)


@bridge_view("people_who_exist", kind=KEYED)
def people_who_exist(sim, trade):
    return sim.labour.people_who_exist(trade)


@bridge_view("reachable_trade_population", kind=KEYED)
def reachable_trade_population(sim, trade):
    return sim.labour.reachable_trade_population(trade)


@bridge_view("local_market_share")
def local_market_share(sim):
    return sim.labour.local_market_share()


@bridge_view("base_tile", seat_scoped=True)
def base_tile(sim):
    """Where the acting seat works from."""
    return sim.labour.base_tile()


@bridge_view("trades_absent")
def trades_absent(sim):
    """The trades nobody practises at the opening."""
    return TRADES_ABSENT


@bridge_view("concern_staff", kind=KEYED)
def concern_staff(sim, node_id):
    """People of each trade one plant of the concern needs."""
    return sim.concern_staff_by_trade(node_id)


@bridge_command(ReleaseStaff)
def release_staff(sim, command):
    with sim.act_as(command.seat_id):
        sim.labour.fire(command.trade, command.people)


# ---- production: concerns, their takings and the industry's experience ----


@bridge_view("concern_takings", kind=QUOTE)
def concern_takings(sim, node_id, ramp, **options):
    return sim.concern_takings(node_id, ramp, **options)


@bridge_view("concern_gross", kind=QUOTE)
def concern_gross(sim, node_id):
    return sim.economy.concern_gross(node_id)


@bridge_view("concern_upkeep", kind=QUOTE)
def concern_upkeep(sim, node_id, capacity=1.0, **options):
    return sim.economy.concern_upkeep(node_id, capacity, **options)


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


@bridge_view("unit_mass_kg", kind=QUOTE)
def unit_mass(sim, material):
    return unit_mass_kg(material)


@bridge_view("seat_review", kind=QUOTE)
def seat_review(sim, world, year):
    """The founder's seat's answers to a business review (engine/projects_review.py)."""
    return SeatReview(world, year, sim)


@bridge_command(AccrueExperience)
def accrue_experience(sim, command):
    sim.accrue_industry_experience()


# ---- markets: goods categories, the agent economy's book and the orders the actors place ----


@bridge_view("goods_category_factor", kind=QUOTE)
def goods_category_factor(sim, category):
    return sim.goods_category_factor(category)


@bridge_view("goods_category_factor_with_entrants", kind=QUOTE)
def goods_category_factor_with_entrants(sim, category, entrants):
    return sim.goods_category_factor_with_entrants(category, entrants)


@bridge_view("goods_category_price_ratio", kind=KEYED)
def goods_category_price_ratio(sim, category):
    return sim.goods_category_price_ratio(category)


@bridge_view("goods_category_state", kind=KEYED)
def goods_category_state(sim, category):
    return sim._goods_category_state(category)


@bridge_view("nodes_in_category", kind=KEYED)
def nodes_in_category(sim, category):
    return sim._nodes_in_cat(category)


@bridge_view("market_state", kind=KEYED)
def market_state(sim, commodity):
    return sim.market_state(commodity)


@bridge_view("commodities_sold_by_acting_party")
def commodities_sold_by_acting_party(sim):
    return sim.economy.goods.commodities_sold_by(sim.goods_market.acting_party_id)


@bridge_view("economy_output_value")
def economy_output_value(sim):
    return sim.economy.output_value()


@bridge_view("coin_stock_value")
def coin_stock_value(sim):
    return sim.economy.coin_stock_value()


@bridge_view("main_material_of", kind=KEYED)
def main_material_of(sim, commodity):
    return sim.economy.main_material_of(commodity)


@bridge_view("material_trade_quote", kind=KEYED)
def material_trade_quote(sim, material):
    return sim.economy.trade_quote(material)


@bridge_view("material_purchase_cost", kind=QUOTE)
def material_purchase_cost(sim, material, tonnes):
    """(money, mean money per tonne) to buy `tonnes`; None when the material has no price."""
    return sim.economy.purchase_cost(material, tonnes)


@bridge_view("materials_serving", kind=KEYED)
def materials_serving(sim, need_id):
    from . import need_substitutes
    return need_substitutes.serving(need_id)


@bridge_view("household_basket")
def household_basket(sim):
    return market_demand.household_basket(sim.civ, sim.world_map)


@bridge_view("agent_trades_good", kind=KEYED)
def agent_trades_good(sim, material):
    return sim.economy.agent_trades_good(material)


@bridge_view("agent_price_response", kind=QUOTE)
def agent_price_response(sim, material, landed_tonnes, taken_tonnes):
    return sim.economy.agent_price_response(material, landed_tonnes, taken_tonnes)


@bridge_view("agent_country", kind=KEYED)
def agent_country(sim, country):
    return sim.economy.agent_country(country)


@bridge_view("agent_cohort_incomes")
def agent_cohort_incomes(sim):
    return sim.economy.agent_cohort_incomes()


@bridge_view("agent_cohort_land_rents", kind=QUOTE)
def agent_cohort_land_rents(sim, tiles):
    return sim.economy.agent_cohort_land_rents(tiles)


@bridge_view("agent_need_floor_costs")
def agent_need_floor_costs(sim):
    return sim.economy.agent_need_floor_costs()


@bridge_view("agent_land_rent_at", kind=QUOTE)
def agent_land_rent_at(sim, tile):
    return sim.economy.agent_land_rent_at(tile)


@bridge_view("agent_land_rent_paid_by_tile")
def agent_land_rent_paid_by_tile(sim):
    return sim.economy.agent_land_rent_paid_by_tile()


@bridge_view("agent_land_rent_per_hectare")
def agent_land_rent_per_hectare(sim):
    return sim.economy.agent_land_rent_per_hectare()


@bridge_view("agent_output_tonnes_by_tile")
def agent_output_tonnes_by_tile(sim):
    return sim.economy.agent_output_tonnes_by_tile()


@bridge_view("agent_idle_hours_by_trade")
def agent_idle_hours_by_trade(sim):
    return sim.economy.agent_idle_hours_by_trade()


@bridge_view("agent_fugitive_share_by_tile")
def agent_fugitive_share_by_tile(sim):
    """{tile: share of its people away having fled the state's take}; empty before the agent economy exists."""
    agent = sim.economy.agent
    return {} if agent is None else agent.fugitive_share_by_tile()


@bridge_view("country_opening_basket", kind=KEYED)
def country_opening_basket(sim, country):
    return sim.economy.agent_opening_basket(country)


@bridge_view("country_volume_baseline", kind=KEYED)
def country_volume_baseline(sim, country):
    return sim.economy.agent_volume_baseline(country)


@bridge_view("country_traded_volumes", kind=KEYED)
def country_traded_volumes(sim, country):
    return sim.economy.agent_traded_volumes(country)


@bridge_view("fleet_goods", kind=QUOTE)
def fleet_goods(sim, holder_id):
    return sim.economy.fleet_goods(holder_id)


@bridge_command(ForgetActorOrders)
def forget_actor_orders(sim, command):
    sim.economy.forget_actor_orders(command.actor_id)


@bridge_command(NoteActorSale)
def note_actor_sale(sim, command):
    sim.economy.note_actor_sale(command.seller_id, command.material, command.tonnes, command.from_concerns)


@bridge_command(NoteActorPurchase)
def note_actor_purchase(sim, command):
    sim.economy.note_actor_purchase(command.buyer_id, command.commodity, command.tonnes, command.budget)


# ---- finance ----


@bridge_view("credit_room", kind=QUOTE)
def credit_room(sim, actor_id):
    return sim.economy.credit_room(actor_id)


@bridge_view("state_lending")
def state_lending(sim):
    return sim.state_lending()


@bridge_view("debt_interest_rate")
def debt_interest_rate(sim):
    return sim.debt_interest_rate()


@bridge_view("debt_service_share_of_surplus")
def debt_service_share_of_surplus(sim):
    return DebtServiceMixin.DEBT_SERVICE_SHARE_OF_SURPLUS


@bridge_command(RefreshLenderOffers)
def refresh_lender_offers(sim, command):
    sim.refresh_lender_offers()


@bridge_command(DefaultOnDebt)
def default_on_debt(sim, command):
    sim.default_on_debt(command.year)


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


@bridge_view("border_duty_per_tonne", kind=QUOTE)
def border_duty_per_tonne(sim, source, destination, price_per_tonne):
    """Money the destination country's state charges on a tonne bought at `price_per_tonne` in `source`; infinite on an embargo."""
    return trade_duty.duty_per_tonne(sim, source, destination, price_per_tonne)
