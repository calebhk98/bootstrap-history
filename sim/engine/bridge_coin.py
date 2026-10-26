"""Bridge entries the coin module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the
entry is deleted. `legacy_agent_world` is raw state the module still reads in place (the agent economy's world)."""
from sim.assembly.api import KEYED, QUOTE
from sim.geography.api import route as route_over_tiles
from sim.geography.api import usable_modes as usable_route_modes
from sim.ledger.api import STORE_ACTOR, STORE_GRANARY, STORE_STOCK, TakeGoods

from .bridge import bridge_command, bridge_view
from .data import load_civ, starting_schedule
from .foreign_routes import route_from_geography


# ---- workforce and markets ----

@bridge_view("opening_money_per_labour_hour")
def opening_money_per_labour_hour(sim):
    return sim.labour.opening_wage_schedule().opening_money_per_labour_hour


@bridge_view("headcount", seat_scoped=True)
def headcount(sim):
    return sim.labour.headcount()


@bridge_view("opening_population")
def opening_population(sim):
    return sim._opening_population()


@bridge_view("goods_quote", kind=KEYED)
def goods_quote(sim, material):
    """The market's buy and sell terms for a tonne of a material, or None when it has no price."""
    return sim.goods_market.quote(material)


# ---- foreign trade ----

@bridge_view("foreign_economies")
def foreign_economies(sim):
    return sim.foreign_economies()


@bridge_view("foreign_coin_home_units")
def foreign_coin_home_units(sim):
    """Coin units the home society gained (negative: paid out) in trade with every partner."""
    return sum(ledger["home_coin_units"] for ledger in sim.state.economy.foreign_ledger.values())


@bridge_view("foreign_coin_partner_units", kind=KEYED)
def foreign_coin_partner_units(sim, civilization_id):
    """Coin units a partner gained (negative: paid out) in trade with the home society; none where nothing is booked."""
    return sim._foreign_ledger(civilization_id)["partner_coin_units"]


@bridge_view("partner_coin_standard", kind=KEYED)
def partner_coin_standard(sim, civilization_id):
    return sim.partner_civ(civilization_id)["coin_standard"]


@bridge_view("partner_opening_facts", kind=KEYED)
def partner_opening_facts(sim, civilization_id):
    """{population, money_per_labour_hour}: what a partner's opening coin stock is sized from."""
    return {"population": load_civ(civilization_id).get("population"),
            "money_per_labour_hour": starting_schedule(civilization_id).money_per_labour_hour}


@bridge_view("partner_route_cost", kind=KEYED)
def partner_route_cost(sim, civilization_id):
    """Home money to carry a tonne over the route to a partner; None where no route is known."""
    route = sim._foreign_economy_facts(civilization_id)["route"]
    return None if route is None else route.cost_per_tonne


# ---- reporting ----

@bridge_view("coin_value_ratio", kind=KEYED)
def coin_value_ratio(sim, metal):
    """What the coin of this metal buys now over what it bought at the baseline; one while the economy opens."""
    return sim.coin_value_ratio(metal)


# ---- finance, polity, agriculture, resources ----

@bridge_view("lent_share")
def lent_share(sim):
    return sim.lent_share()


@bridge_view("visible_scale", kind=QUOTE)
def visible_scale(sim, headcount_of_holder, wealth, eminence_of_holder):
    return sim.visible_scale(headcount_of_holder, wealth, eminence_of_holder)


@bridge_view("order_reach")
def order_reach(sim):
    return sim.order_reach()


@bridge_view("eminence", seat_scoped=True)
def eminence(sim):
    return sim.state.household.eminence


@bridge_view("farm_holdings", seat_scoped=True)
def farm_holdings(sim):
    """{hectares: farmland held, or None before a farm; stock_kg: the granary}."""
    return {"hectares": sim.state.holdings.farm_hectares, "stock_kg": sim.farm_stock_kg}


@bridge_view("farm_land_price")
def farm_land_price(sim):
    return sim.farm_price_per_hectare()


@bridge_view("forest_holding", seat_scoped=True)
def forest_holding(sim):
    """{hectares, base_cost_per_hectare, price_index}: the forest held and what a hectare costs, before the price index."""
    return {"hectares": sim.forest_ha, "base_cost_per_hectare": sim.FOREST_COST_PER_HA, "price_index": sim.price_index}


# ---- land ----

@bridge_view("home_country")
def home_country(sim):
    """{id: the home country's id, location: the tile at its centre, None when the cast has no such country}."""
    state = sim.actors.state
    home = state.countries.get(state.home_country)
    return {"id": state.home_country, "location": None if home is None else home.location}


@bridge_view("tile_known", kind=KEYED)
def tile_known(sim, tile):
    return tile in sim.world_map.tiles


@bridge_view("tile_haul_cost", kind=QUOTE)
def tile_haul_cost(sim, origin, destination):
    """Home money to haul a tonne over the cheapest route between two tiles; nothing where none joins them. Remembered
    for the year."""
    cache = sim.__dict__.setdefault("_home_carriage_cache", {})
    year = sim.state.scenario.year
    if cache.get("year") != year:
        cache.clear()
        cache["year"] = year
    key = (origin, destination)
    if key not in cache:
        home_techs = sim.held_and_running(include_starting=False)
        mode_costs = sim._freight_mode_costs(0.0)
        modes = [mode for mode in usable_route_modes((home_techs,), sim.world_map) if mode in mode_costs]
        found = route_over_tiles([origin], [destination], modes, mode_costs=mode_costs,
                                 handling_costs=sim._freight_handling_costs(), held_nodes=home_techs,
                                 world_map=sim.world_map)
        cache[key] = 0.0 if found is None else sim._with_carried_provisions(
            route_from_geography(found)).cost_per_tonne
    return cache[key]


# ---- actors ----

@bridge_view("legacy_agent_world")
def agent_world(sim):
    from .agents_port import SimWorld
    return SimWorld(sim)


# ---- commands ----

@bridge_command(TakeGoods)
def take_goods(sim, command):
    """Thieves take tonnes of a good out of a holder's store, never below zero, into an edge's goods."""
    if command.store == STORE_ACTOR:
        stores = sim.actors.actors[command.actor].record.stores
        stores[command.good] = max(0.0, stores[command.good] - command.tonnes)
    elif command.store == STORE_STOCK:
        stock = sim._material_stock()
        stock[command.good] = max(0.0, stock[command.good] - command.tonnes)
    elif command.store == STORE_GRANARY:
        sim.farm_stock_kg = max(0.0, sim.farm_stock_kg - command.tonnes * 1000.0)
    sim.edge(command.edge).receive_goods(command.good, command.tonnes)
