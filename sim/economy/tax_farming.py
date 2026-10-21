"""Tax farming: a state lets the right to collect a money form of revenue for a year to the best bidder.

The state names the forms to farm (`YearInputs.farmed_forms`, its choice through its decision policy). Any
actor holding cash may bid: it expects the form's base of last year taxed at its own reach, discounted at the
market rate for waiting a year, and offers no more than it holds. The highest bid at or above what the state
expects to collect itself, discounted the same way, wins. The farmer pays the state its price at once, then
collects the form from the payers through the ordinary assessment (taxes.py) at its own reach; the surplus
or loss is its own. The lease lasts the year it is struck.
"""
from typing import Dict, List, Sequence, Tuple

from sim.constants import declare

from .types import AgentId, Transfer, is_edge

TAX_FARMER_REACH = declare(
    "TAX_FARMER_REACH", 0.9, kind="temporary_heuristic",
    unit="share of each liability a farmer's own collectors can assess and collect",
    source=None, confidence="D",
    why="A farmer collects with its own agents, locally; how far its writ runs depends on the staff it hires "
        "and the force it can call on, which are not modelled. The state's own reach is its capacity.",
    retire="Complaints/660: state officials and collectors as actors")


def expected_take(rate: float, base: float, reach: float) -> float:
    """What a collector expects from a form: the form's rate on last year's base, at its reach."""
    return rate * base * reach


def reserve_price(state_take: float, interest_rate: float) -> float:
    """The least the state accepts: what it expects to collect itself, discounted a year."""
    return state_take / (1.0 + max(0.0, interest_rate))


def bids(record, form, interest_rate: float, state_agent: AgentId, currency: str,
         reach: float = TAX_FARMER_REACH) -> List[Tuple[float, float, AgentId]]:
    """(price, cash, bidder) for every actor holding cash, best first: the price is what the bidder expects
    to take, discounted a year, and no more than its cash. Empty without a year of history to expect from."""
    history = record.tax_history.get(form.name)
    if not history or history["base"] <= 0.0:
        return []
    worth = expected_take(form.rate, history["base"], reach) / (1.0 + max(0.0, interest_rate))
    offers = []
    for agent in sorted(record.book.agents()):
        cash = record.book.balance(agent, currency)
        if is_edge(agent) or agent == state_agent or cash <= 0.0:
            continue
        offers.append((min(worth, cash), cash, agent))
    return sorted(offers, key=lambda offer: (-offer[0], -offer[1], offer[2]))


def run_auctions(setup, record, form_names: Sequence[str], interest_rate: float) -> Dict[str, dict]:
    """Strike this year's leases for the named money forms. The winner pays the state at once. Returns the
    leases struck (form -> farmer and price), which also stand in `record.tax_farms` until the year's
    collection (year_close.money_taxes)."""
    record.tax_farms = {}
    forms = {form.name: form for form in setup.tax_forms if not form.paid_in}
    for name in sorted(set(form_names)):
        form = forms.get(name)
        history = record.tax_history.get(name)
        if form is None or not history:
            continue
        offers = bids(record, form, interest_rate, setup.state_agent, setup.currency_id)
        if not offers:
            continue
        price, _cash, farmer = offers[0]
        if price <= 0.0 or price < reserve_price(history["state_take"], interest_rate):
            continue
        record.book.transfer(Transfer(farmer, setup.state_agent, setup.currency_id, price, "tax_farm:" + name))
        record.tax_farms[name] = {"farmer": farmer, "price": price}
    return dict(record.tax_farms)


def remember_year(record, assessments, farmed_names: Sequence[str], state_capacity: float,
                  reach: float = TAX_FARMER_REACH) -> None:
    """Keep each form's base and what the state would have collected at its own reach, for next year's bids
    and reserve. A farmed form's take is scaled from the farmer's reach back to the state's."""
    for assessment in assessments:
        farmed = assessment.form in farmed_names
        state_take = assessment.collected_value * (state_capacity / reach if farmed and reach > 0.0 else 1.0)
        record.tax_history[assessment.form] = {"base": assessment.base_value, "state_take": state_take}
