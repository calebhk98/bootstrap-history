"""Bridge entries the materials module reads, and the market commands it sends, until the owners behind them move into modules.

Each view carries the name its owner will publish (docs/architecture/catalogue), asks the engine exactly as the old code
did, and is never cached."""
from sim.assembly.api import KEYED, QUOTE
from sim.markets.api import NoteDraw, NotePurchase, ResetDraws

from . import purchase_rule
from .bridge import bridge_command, bridge_view
from .data import hard_pre
from .goods_market_imports import HOME_SELLER


# ---- the tree and the seat's projects ----

@bridge_view("hard_prerequisites", kind=KEYED)
def hard_prerequisites(sim, node_id):
    """Every prerequisite of a node that is mandatory: its `pre`, and the requirement groups that offer one real node."""
    return hard_pre(sim.nodes, node_id)


@bridge_view("project_versions", seat_scoped=True)
def project_versions(sim):
    """(the acting seat's active-projects version, its done-set version): move when a project starts, finishes or is lost."""
    return (sim.household.active_version, sim.household.done_version)


@bridge_view("empire_output")
def empire_output(sim):
    """The reference empire's yearly output of the tracked commodities, by commodity: {"t_per_yr": ...}."""
    return sim.res["empire_output_100ad"]


# ---- the catalogue of commodities, the price epoch and the producers ----

@bridge_view("material_commodity_map")
def material_commodity_map(sim):
    """{material key: curated commodity id} from the commodity catalogue."""
    return sim._material_commodity_map()


@bridge_view("commodity_country_output", kind=QUOTE)
def commodity_country_output(sim, commodity):
    """Tonnes a year the society brings to market of a catalogued commodity, which knows what built works raise it."""
    return sim._commodity_ledger().country_output(commodity, built=sim.state.projects.done)


@bridge_view("price_epoch")
def price_epoch(sim):
    """Changes whenever the techniques in use might, or the price level does."""
    return sim.price_epoch()


@bridge_view("producers_stamp")
def producers_stamp(sim):
    """Changes whenever the economy's producers do (as its year closes)."""
    return sim.economy.producers_stamp()


@bridge_view("agent_producer_capacity", kind=KEYED)
def agent_producer_capacity(sim, material):
    """Tonnes a year the agent economy's producers can make of a material; None while the economy opens."""
    return sim.economy.agent_producer_capacity_tonnes(material)


# ---- the goods market ----

@bridge_view("partner_import", kind=KEYED)
def partner_import(sim, material):
    """(the partner that sells a material, the tonnes it can still bring this year); (None, None) when the home society is
    its seller or no one is. The tonnes are None when the route has no figure."""
    market = sim.goods_market
    seller = market.offered_by(material)
    if seller is None or seller == HOME_SELLER:
        return (None, None)
    return (seller, market.import_tonnes_available(material, seller))


@bridge_view("can_be_bought", kind=KEYED)
def can_be_bought(sim, material):
    """Whether anyone in reach sells the material at a price."""
    return sim.goods_market.can_be_bought(material)


@bridge_view("purchase_quote", kind=QUOTE)
def purchase_quote(sim, material, tonnes, already=0.0):
    """(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled; None when
    it has no price."""
    return sim.goods_market.quote_buy(material, tonnes, already)


@bridge_command(ResetDraws)
def reset_draws(sim, command):
    sim.goods_market.reset_draws()


@bridge_command(NoteDraw)
def note_draw(sim, command):
    sim.goods_market.note_draw(command.commodity, command.tonnes)


@bridge_command(NotePurchase)
def note_purchase(sim, command):
    sim.goods_market.note_purchase(sim.goods_market.acting_party_id, command.commodity, command.tonnes)


# ---- projects' costs and what the seat can pay ----

@bridge_view("shared_bill", kind=QUOTE)
def shared_bill(sim, node_id, compute):
    """A project's material bill, reused inside a view's scope while the world and the node's stock hold."""
    return sim._shared_bill(node_id, compute)


@bridge_view("project_cost_now", kind=QUOTE)
def project_cost_now(sim, node_id):
    return sim.project_cost_now(node_id)


@bridge_view("opposition_factor", kind=QUOTE)
def opposition_factor(sim, node_id):
    return sim.opposition_factor(node_id)


@bridge_view("cost_money_factor")
def cost_money_factor(sim):
    return sim.cost_money_factor()


@bridge_view("failure_reset_share")
def failure_reset_share(sim):
    """The share of a failed project's bill that is lost."""
    return sim.FAILURE_RESET_SHARE


@bridge_view("material_cost_factor", kind=QUOTE)
def material_cost_factor(sim, node_id):
    """What the geography multiplies a project's material bill by (distance from the sources)."""
    return sim.geography.material_cost_factor(node_id)


@bridge_view("purchase_refusal", kind=QUOTE)
def purchase_refusal(sim, what, cost):
    """The refusal that states the purchase rule, the budget and the amount short."""
    return purchase_rule.refusal_text(sim, what, cost)
