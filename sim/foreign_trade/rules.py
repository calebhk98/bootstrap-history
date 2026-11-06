"""Foreign trade's rules as plain functions of their inputs."""
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from sim.world import balance_of_payments

from .constants import (BOUGHT, LANDED, LANDED_COST, LANDING, LEDGER_FIELDS, SOLD, TAKEN, TAKING, THROUGH,
                        TRADE_YEARS_KEPT)


# ---- which economies trade ----

def partner_countries(records: Iterable[Mapping[str, Any]], year: int, own: Optional[str], replaced: Optional[str]) -> List[str]:
    """Every economy enabled for `year`, sorted by id. The society itself is not its own partner, and a variant stands in
    for its base: the base is not also a partner."""
    return sorted(record["civilization"] for record in records
                  if record.get("enabled", False) and record["civilization"] not in (own, replaced)
                  and record["from_year"] <= year <= record["until_year"])


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
