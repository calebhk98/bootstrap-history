"""The markets module's spec (sim/assembly).

The engine's market objects (`Sim.economy` over the agent economy, `Sim.goods_market`) and the mixins that clear the year have
not moved into the module yet, so it reaches them through `legacy_game` and every view it publishes is uncached: the
engine still writes the book, the flows and the agent economy's record directly."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .commands import ForgetActorOrders, NoteActorPurchase, NoteActorSale, NoteDraw, NotePurchase, ResetDraws
from .module import Markets

READS_BY_OWNER = {
	"core": ("legacy_game",),
	"materials": ("material_commodity",),
}

_LIVE = dict(cached=False)

# (name, kind) of every view; the module method that computes it has the view's name
_VIEWS = (
	("goods_quote", KEYED), ("material_trade_quote", KEYED), ("material_purchase_cost", QUOTE), ("purchase_quote", QUOTE),
	("can_be_bought", KEYED), ("material_seller", KEYED), ("partner_import", KEYED), ("home_unit_price", KEYED),
	("household_prices", None), ("commodities_sold_by_acting_party", None), ("main_material_of", KEYED),
	("market_state", KEYED), ("market_floor_ratio", KEYED), ("opening_population", None), ("new_goods_units", None),
	("goods_category_factor", QUOTE), ("goods_category_factor_with_entrants", QUOTE), ("goods_category_price_ratio", KEYED),
	("goods_category_state", KEYED), ("nodes_in_category", KEYED), ("actor_supply", KEYED), ("actor_demand", KEYED),
	("agent_prices", None), ("agent_wage", KEYED), ("agent_unskilled_wage", None), ("agent_people_by_trade", None),
	("agent_people_by_tile_and_trade", None), ("agent_land_rent", None), ("agent_land_rent_per_hectare", None),
	("agent_land_rent_at", QUOTE), ("agent_land_rent_paid_by_tile", None), ("agent_trades_good", KEYED),
	("agent_price_response", QUOTE), ("agent_country", KEYED), ("agent_cohort_incomes", None),
	("agent_cohort_land_rents", QUOTE), ("agent_need_floor_costs", None), ("agent_output_tonnes_by_tile", None),
	("agent_idle_hours_by_trade", None), ("agent_fugitive_share_by_tile", None), ("agent_opening_basket", None),
	("agent_volume_baseline", None), ("agent_traded_volumes", None), ("agent_producer_capacity", KEYED),
	("producers_stamp", None), ("producer_capacities", None), ("goods_carried_last_year", None),
	("country_opening_basket", KEYED), ("country_volume_baseline", KEYED), ("country_traded_volumes", KEYED),
	("fleet_goods", QUOTE), ("economy_output_value", None), ("coin_stock_value", None),
)


def _view(name, kind):
	return ViewSpec(name, name, **_LIVE) if kind is None else ViewSpec(name, name, kind=kind, **_LIVE)


MODULE_SPECS = (ModuleSpec(
	"markets", Markets,
	publishes=tuple(_view(name, kind) for name, kind in _VIEWS),
	applies=((ResetDraws, "reset_draws"), (NoteDraw, "note_draw"), (NotePurchase, "note_purchase"),
	         (ForgetActorOrders, "forget_actor_orders"), (NoteActorSale, "note_actor_sale"),
	         (NoteActorPurchase, "note_actor_purchase")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
),)
