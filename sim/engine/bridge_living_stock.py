"""Bridge entries the living-stock and defence-stores modules use until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the
entry is deleted. The `partner_*` views carry the foreign-trade and polity arithmetic that used to sit in the
living-stock mixins (a partner's landed price, the carriage of a smuggled load, a state's chance to catch it)."""
from sim.foreign_trade.api import CloseMarketsTo, RecordStockTaken, SettleFlow
from sim.polity.api import RaiseScandal
from sim.workforce.api import PressLabour
from sim.assembly.api import KEYED, QUOTE
from sim.world import stock_dynamics
from sim.world.material_units import tonnes_per_unit

from . import purchase_rule
from .bridge import bridge_command, bridge_view
from .hazard_window import hazards_not_yet_past
from sim.coin.api import visibility_factor


# ---- facts of the world and the game's data ----



@bridge_view("civilisation")
def civilisation(sim):
    return sim.civ




@bridge_view("material_commodity", kind=KEYED)
def material_commodity(sim, material):
    """The commodity key a material is held under in the tonnes ledger."""
    return sim._material_tag(material)[0]


@bridge_view("producer_capacities")
def producer_capacities(sim):
    return sim.economy.producer_capacities()


# ---- land ----

@bridge_view("stock_land")
def stock_land(sim):
    """{place: the tile the held stock stands on, pasture_kg: live weight the held tiles' grass carries}."""
    return {"place": sim.geography.stock_place(), "pasture_kg": sim.geography.held_pasture_kg(sim.view("wild_stock")())}


@bridge_view("endemic_stock_loss", kind=QUOTE)
def endemic_stock_loss(sim, place, species):
    return sim.geography.endemic_stock_loss(place, species)


@bridge_view("nursery_room_units", kind=QUOTE)
def nursery_room_units(sim, place, output_per_batch, hectare_years_per_batch):
    return sim.geography.nursery_room_units(place, output_per_batch, hectare_years_per_batch)


# ---- labour and money ----

@bridge_view("hour_wage", kind=KEYED)
def hour_wage(sim, trade):
    """Money one hour of a trade costs now."""
    return sim.labour.market.quote(trade)


@bridge_view("can_pay", kind=QUOTE)
def can_pay(sim, cost):
    """Whether the acting seat's purchase budget covers `cost`."""
    return purchase_rule.can_pay(sim, cost)


@bridge_view("hours_per_person_year")
def hours_per_person_year(sim):
    return sim.HOURS_PER_PERSON_YEAR




@bridge_command(PressLabour)
def press_labour(sim, command):
    sim.labour.market.press(command.trade, command.hours)


@bridge_command(RaiseScandal)
def raise_scandal(sim, command):
    sim.scandal += command.scandal
    if sim.scandal_last_year is not None:
        sim.scandal_last_year += command.scandal


# ---- partners ----

@bridge_view("partners")
def partners(sim):
    return sim.partner_countries()


@bridge_view("partner", kind=KEYED)
def partner(sim, civilization_id):
    """{civ: the partner's civilisation record, has_government, stock_taken: {material: units smugglers took}}."""
    government = sim.partner_government(civilization_id)
    return {"civ": sim.partner_civ(civilization_id), "has_government": government is not None,
            "stock_taken": {} if government is None else dict(government.record.stock_taken)}


@bridge_view("partner_refusal", kind=QUOTE)
def partner_refusal(sim, civilization_id, material):
    return sim.partner_refusal(civilization_id, material)


@bridge_view("partner_gate", kind=QUOTE)
def partner_gate(sim, civilization_id):
    return sim.partner_gate_refusal(civilization_id)


@bridge_view("partner_landed_price", kind=QUOTE)
def partner_landed_price(sim, civilization_id, material):
    """Home money per tonne delivered from a partner, or None when it cannot supply it."""
    if civilization_id not in sim.partner_countries() or sim.partner_refusal(civilization_id, material):
        return None
    facts = sim._foreign_economy_facts(civilization_id)
    price = facts["prices_in_home_money"].get(material)
    if material not in facts["solved_materials"] or not price:
        return None
    route = sim.view("material_route")(sim.partner_civ(civilization_id), material, facts["route"])
    if route is None:
        return None
    per_tonne = price / tonnes_per_unit(material) * sim.partner_price_level(civilization_id)
    return (per_tonne * (1.0 + sim.view("trader_cost_share")(route, material, civilization_id))
            + sim.view("trader_agent_cost")(civilization_id, route) + route.cost_per_tonne)


@bridge_view("partner_carry", kind=QUOTE)
def partner_carry(sim, civilization_id, material):
    """(money per tonne to carry a load out of a partner by the agents at the two ends and the freight, the share
    the route loses on the way)."""
    facts = sim._foreign_economy_facts(civilization_id)
    carry_per_tonne = sim.view("trader_agent_cost")(civilization_id, facts["route"]) + facts["freight_per_tonne"]
    return carry_per_tonne, sim.view("cargo_lost_share")(facts["route"], material, civilization_id)


@bridge_view("partner_catch_chance", kind=QUOTE)
def partner_catch_chance(sim, civilization_id, share_of_holding):
    """Chance the partner's state finds out a taking of this share of what it holds: its reach (what its paid
    officials collect of what is due over its roads) against how visible the bite is."""
    from .agents_port import SimWorld
    from .agents_port_cast import seed_opening_cast
    seed_opening_cast(sim)
    reach = float(sim.actors.world_for(sim.partner_government(civilization_id), SimWorld(sim)).state_reach())
    return stock_dynamics.catch_chance(reach, visibility_factor(share_of_holding))


@bridge_command(SettleFlow)
def settle_flow(sim, command):
    """Pay the partner in its own coin's metal and note the flow."""
    coin = sim.partner_civ(command.partner)["coin_standard"]
    coin_price = sim.goods_market.home_unit_price(coin["material"])
    if coin_price:
        sim._settle_flow(command.partner, command.tonnes, command.value, coin["kg_per_unit"] * coin_price)


@bridge_command(RecordStockTaken)
def record_stock_taken(sim, command):
    government = sim.partner_government(command.partner)
    if government is not None:
        taken = government.record.stock_taken
        taken[command.material] = taken.get(command.material, 0.0) + command.units


@bridge_command(CloseMarketsTo)
def close_markets_to(sim, command):
    government = sim.partner_government(command.partner)
    if government is not None:
        government.close_markets_to(command.party, command.until)


# ---- what is built and running ----

@bridge_view("techniques_done")
def techniques_done(sim):
    return sim.state.projects.done


@bridge_view("operating")
def operating(sim):
    return sim.state.projects.operating




@bridge_view("institution_units", kind=KEYED)
def institution_units(sim, node_id):
    return sim.institution_units(node_id)


@bridge_view("live_hazard_kinds", kind=QUOTE)
def live_hazard_kinds(sim, year_now):
    """The kinds of hazard in progress in `year_now`."""
    return {kind for hazard, _start, _end, in_progress in hazards_not_yet_past(sim.civ, year_now)
            if in_progress for kind in hazard}
