"""Foreign trade's rules as plain functions of their inputs."""
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from sim.world import balance_of_payments, market

from .constants import (BOUGHT, LANDED, LANDED_COST, LANDING, LEDGER_FIELDS, SOLD, TAKEN, TAKING, THROUGH,
                        TRADE_YEARS_KEPT)


# ---- which economies trade ----

def partner_countries(records: Iterable[Mapping[str, Any]], year: int, own: Optional[str], replaced: Optional[str]) -> List[str]:
    """Every economy enabled for `year`, sorted by id. The society itself is not its own partner, and a variant stands in
    for its base: the base is not also a partner."""
    return sorted(record["civilization"] for record in records
                  if record.get("enabled", False) and record["civilization"] not in (own, replaced)
                  and record["from_year"] <= year <= record["until_year"])


def agent_economy_ids(records: Iterable[Mapping[str, Any]]) -> set:
    """Ids of the economies whose tiles, people and producers are in the agent economy itself."""
    return {record["civilization"] for record in records if record.get("agent_economy", False)}


# ---- the partner's ledger ----

def blank_ledger() -> Dict[str, float]:
    return {field: 0.0 for field in LEDGER_FIELDS}


def note_trade_value(by_year: Dict[str, Dict[str, float]], year: int, flow_tonnes: float, value: float) -> None:
    """Add a flow's value to this year's imports or exports; only the last few years are kept."""
    entry = by_year.setdefault(str(year), {"in": 0.0, "out": 0.0})
    entry["in" if flow_tonnes > 0.0 else "out"] += value
    for old in [key for key in by_year if int(key) <= year - TRADE_YEARS_KEPT]:
        del by_year[old]


def import_payment(value: float, home_coin_stock_units: float, home_money_per_partner_coin: float) -> Tuple[float, float]:
    """(coin the home society pays, coin units the partner receives) for imports worth `value` of home money."""
    paid = balance_of_payments.coin_paid(value, home_coin_stock_units)
    return paid, paid / home_money_per_partner_coin


def book_import(ledger: Dict[str, float], paid: float, received: float, carriage: float, home_money_per_partner_coin: float) -> None:
    """The route's carriers are the home economy's (freight is priced in home money), so their pay stays in the home stock."""
    ledger["home_coin_units"] -= paid - carriage * home_money_per_partner_coin
    ledger["partner_coin_units"] += received - carriage
    ledger["coin_carriage_units"] += carriage


def export_payment(value: float, partner_coin_stock_units: float, home_money_per_partner_coin: float) -> float:
    """Coin units the partner pays for exports worth `value` of home money, never more than it holds."""
    return balance_of_payments.coin_paid(value / home_money_per_partner_coin, partner_coin_stock_units)


def book_export_paid(ledger: Dict[str, float], paid_units: float) -> None:
    """The partner pays out coin; booked before the carriage is priced, which reads what the partner holds."""
    ledger["partner_coin_units"] -= paid_units


def book_export(ledger: Dict[str, float], paid_units: float, carriage: float, home_money_per_partner_coin: float) -> None:
    ledger["home_coin_units"] += paid_units * home_money_per_partner_coin   # sellers and carriers, both home
    ledger["coin_carriage_units"] += carriage


def lift_years_per_tonne(cargo_tonnes: float, working_days: float, days_on_leg: float) -> float:
    """Carrier-years a leg uses to move a tonne one way: a round trip, empty back."""
    return 2.0 * days_on_leg / (cargo_tonnes * working_days)


def route_lift_years_per_tonne(legs: Sequence[Tuple[Any, float, float]]) -> Optional[float]:
    """Carrier-years of lift one tonne a year over the whole route needs; `legs` is (carrier inputs, working days a year,
    days on the leg) for each leg; None for no route."""
    if not legs:
        return None
    total = 0.0
    for inputs, working_days, days_on_leg in legs:
        total += lift_years_per_tonne(inputs.cargo_tonnes, working_days, days_on_leg)
    return total


def route_capital_per_lift_tonne(legs: Sequence[Tuple[Any, Any, float, float]]) -> float:
    """Money of carriers one tonne a year of lift over the route needs; `legs` is (carrier inputs, carrier prices, working
    days a year, days on the leg) for each leg."""
    total = 0.0
    for inputs, prices, working_days, days_on_leg in legs:
        total += lift_years_per_tonne(inputs.cargo_tonnes, working_days, days_on_leg) * (prices.vehicle + prices.animals)
    return total


def lift_capacity(years_per_tonne: Optional[float], recorded_tonnes_per_year: float, opening_carriers: float) -> float:
    """Tonnes a year the route's carriers lift in each direction: infinite for a route of no legs, else the fleet the
    ledger records, else the carriers the route opens with."""
    if years_per_tonne is None:
        return float("inf")
    if recorded_tonnes_per_year > 0.0:
        return recorded_tonnes_per_year
    return opening_carriers / years_per_tonne


def lift_left(ledger: Mapping[str, float], year: int, capacity: float) -> Tuple[float, float]:
    """(into home, out of home) tonnes of lift still free in `year`."""
    if ledger["lift_year"] != year:
        return capacity, capacity
    return max(0.0, capacity - ledger["lift_used_in"]), max(0.0, capacity - ledger["lift_used_out"])


def reset_lift_year(ledger: Dict[str, float], year: int) -> None:
    if ledger["lift_year"] != year:
        ledger["lift_year"] = year
        ledger["lift_used_in"] = ledger["lift_used_out"] = ledger["lift_unmet"] = 0.0


def book_lift(ledger: Dict[str, float], flow_tonnes: float, unmet_tonnes: float) -> None:
    ledger["lift_used_in" if flow_tonnes > 0.0 else "lift_used_out"] += abs(flow_tonnes)
    ledger["lift_unmet"] += unmet_tonnes


# ---- what a partner makes and wants ----

def opening_of_commodity(wanted: float, made: float, tracked_mineral: bool, national_output: float, mineral_share: float,
                         in_balance: float) -> Tuple[float, float]:
    """(capacity tonnes, demand tonnes) a foreign economy opens a commodity with. A mined commodity is its regions' share
    of the national output and its own demand; one nothing can make has no capacity."""
    if tracked_mineral:
        output = national_output * mineral_share
        return output, (output if output > 0.0 else wanted)
    return made * in_balance, wanted


def input_only_supply(national_output: float, partner_population: float, reference_population: float, share: float) -> float:
    """Tonnes a year of a good bought only as an input that a partner holding every technique, input and deposit makes:
    the stated national output scaled by its population."""
    return national_output * (partner_population / reference_population) * share


# ---- the actors' tallies ----

def note_actor_trade(tally: Dict[str, Dict[str, Dict[str, float]]], partner: str, material: str, tonnes: float,
                     to_partner: bool, landed_cost: float = 0.0) -> None:
    """Tally a cargo of `material` an actor carried to (or from) a partner this year; `landed_cost` is what a cargo to the
    partner cost its carrier to land (home money)."""
    flow = tally.setdefault(partner, {}).setdefault(material, {SOLD: 0.0, BOUGHT: 0.0})
    flow[SOLD if to_partner else BOUGHT] += tonnes
    if to_partner:
        before = flow[SOLD] - tonnes
        if tonnes < 0.0 and before > 0.0 and not landed_cost:
            landed_cost = flow.get(LANDED_COST, 0.0) * tonnes / before   # a part of the cargo is taken back: its cost with it
        flow[LANDED_COST] = max(0.0, flow.get(LANDED_COST, 0.0) + landed_cost)


def note_home_trade(tally: Dict[str, Dict[str, float]], material: str, tonnes: float, landing: bool) -> None:
    flow = tally.setdefault(material, {LANDED: 0.0, TAKEN: 0.0})
    flow[LANDED if landing else TAKEN] += tonnes


def home_trade(tally: Mapping[str, Mapping[str, float]], material: str) -> Tuple[float, float]:
    """(tonnes landed in the home market, tonnes taken out of it) by actors so far this year."""
    flow = tally.get(material, {})
    return flow.get(LANDED, 0.0), flow.get(TAKEN, 0.0)


def actors_carry(tally: Mapping[str, Mapping[str, Mapping[str, float]]], material: str, to_partner: bool,
                 partner: Optional[str] = None) -> bool:
    """Whether actors have carried the material this year toward (or from) a partner, any partner by default."""
    key = SOLD if to_partner else BOUGHT
    return any(flows.get(material, {}).get(key, 0.0) > 0.0
               for named, flows in tally.items() if partner is None or named == partner)


def landed_cost(paid: float, carriage: float, market_rate: float) -> float:
    """What a cargo costs its carrier on landing: the purchase, a year's return on it (the carrier's margin) and the
    carriage with its dues."""
    return paid * (1.0 + market_rate) + carriage


def partner_price(price_in_home_money: Optional[float], price_level: float, price_ratio: float) -> Optional[float]:
    """A partner's price of a material in home money: its solved cost, at its coin's price level and the price its own
    market has reached; None when the partner prices nothing of it."""
    if not price_in_home_money:
        return None
    return price_in_home_money * price_level * price_ratio


def import_offers(cargo_by_material: Mapping[str, Mapping[str, float]], commodity_of: Mapping[str, str],
                  tonnes_each: Mapping[str, float], base_prices: Mapping[str, float], price_level: float
                  ) -> Tuple[Dict[str, List[Any]], Dict[str, float]]:
    """The cargo landed at a partner as offers at its landed cost, a ratio to the partner's long-run cost of the material;
    cargo with no landed cost noted is a price taker (returned as plain tonnes)."""
    offers: Dict[str, List[Any]] = {}
    price_taking: Dict[str, float] = {}
    for material, flow in cargo_by_material.items():
        commodity = commodity_of[material]
        base = base_prices.get(material)
        base = base / tonnes_each[material] if base and tonnes_each[material] else None   # per tonne, as the cargo is costed
        tonnes = flow[SOLD]
        if base and tonnes > 0.0 and flow.get(LANDED_COST, 0.0) > 0.0:
            ratio = flow[LANDED_COST] / tonnes / (base * price_level)
            offers.setdefault(commodity, []).append(market.Offer(tonnes, ratio))
        else:
            price_taking[commodity] = price_taking.get(commodity, 0.0) + tonnes
    return offers, price_taking


def clear_partner(entry: Mapping[str, float], floor_ratio: float, ceiling_ratio: float, sold: float, bought: float,
                  imports: Sequence[Any] = ()) -> Any:
    """The partner's market for a commodity cleared on `sold` tonnes landed there at no ask, `imports` landed at their
    landed cost, and `bought` taken from it."""
    return market.clear_market(market.MarketConditions(
        household_demand_at_anchor_tonnes=entry["reference_tonnes"], committed_demand_tonnes=0.0,
        society_capacity_tonnes=entry["capacity_tonnes"], actor_supply_tonnes=sold,
        founder_sales_tonnes=0.0, stock_tonnes=entry["stock_tonnes"], actor_demand_tonnes=bought, imports=tuple(imports),
        floor_ratio=floor_ratio, ceiling_ratio=ceiling_ratio))


def price_response(entry: Mapping[str, float], outcome_price_ratio: float) -> float:
    """Factor on a partner's price once the cargo is cleared in its book."""
    return outcome_price_ratio / entry["price_ratio"]


def close_entry(entry: Dict[str, float], outcome: Any, sold: float, bought: float) -> None:
    """A partner's book entry after its year: capacity follows the price, stock and price follow the clearing."""
    entry["capacity_tonnes"] = market.adjusted_capacity(entry["capacity_tonnes"], outcome.price_ratio)
    entry["stock_tonnes"] = market.stock_after_year(outcome)
    entry["price_ratio"] = outcome.price_ratio
    entry["trade_tonnes"] = sold - bought


def new_entry(demand: float, capacity: float) -> Dict[str, float]:
    return {"reference_tonnes": demand, "capacity_tonnes": capacity,
            "stock_tonnes": 0.0, "price_ratio": 1.0, "trade_tonnes": 0.0}


# ---- the traders' cargo ----

def cargo_kind(destination: str, source: str, home: str) -> Tuple[str, str]:
    """(kind of leg, the partner it is with) for a cargo from `source` to `destination`."""
    kind = LANDING if destination == home else TAKING if source == home else THROUGH
    return kind, (source if kind == LANDING else destination)


def cargo_leg_id(trader_id: str, partner: str, source: str, destination: str, material: str, kind: str) -> str:
    return "cargo:%s:%s:%s:%s" % (trader_id, partner if kind != THROUGH else source + ">" + destination, material, kind)


def blank_leg(leg_id: str, trader_id: str, kind: str, source: str, destination: str, partner: str, material: str) -> Dict[str, Any]:
    return {"id": leg_id, "trader": trader_id, "kind": kind, "source": source, "destination": destination,
            "partner": partner, "material": material, "tonnes": 0.0, "paid": 0.0, "received": 0.0, "carriage": 0.0,
            "duty": 0.0}


def leg_settlement(leg: Mapping[str, Any], result: Optional[Mapping[str, float]]
                   ) -> Tuple[Optional[float], List[Tuple[str, float, float]], float]:
    """How a leg settles against what the agent economy's book gave it (None: the book took none of it, so the leg is
    settled at its quote): (tonnes taken back from a partner's tally or None, the payments as (partner, signed tonnes, value)
    in order, the change to the trader's booking)."""
    kind, tonnes, partner = leg["kind"], leg["tonnes"], leg["partner"]
    delta = 0.0
    taken_back = None
    if kind == LANDING:
        payments = [(partner, tonnes, leg["paid"])]
        if result is not None:
            delta = result["money"] - leg["received"]
    elif kind == TAKING:
        share = 1.0
        if result is not None:
            share = min(1.0, result["tonnes"] / tonnes) if tonnes > 0.0 else 0.0
            delta = leg["received"] * (share - 1.0) + result["money"]
            if share < 1.0:
                taken_back = -tonnes * (1.0 - share)
        payments = [(partner, -tonnes * share, leg["received"] * share)]
    else:
        payments = [(leg["source"], tonnes, leg["paid"]), (leg["destination"], -tonnes, leg["received"])]
    return taken_back, payments, delta
