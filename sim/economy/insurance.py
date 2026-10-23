"""Insurance against a hazard the model has: an insurer (a premium company, or a mutual of its members) pays a holder
the share of its insured value that the hazard took in the year.

The hazard is read as an index (the share of value lost, from the weather the year brought), so a payout needs no
judgement of a single holder's loss and none can cause its own. What a hazard costs is what has been seen of it
(`Hazard`): the mean share lost a year over the years watched, and the worst year. A premium company charges the
mean (its expected claims) plus what it costs to hold capital against the worst year at the market rate; a mutual
charges nothing in advance and its members pay the year's claims between them after it, in proportion to what each
insured. Without a record of the hazard nothing can be priced and no policy is sold.

A company fails the year its purse cannot pay the claims: it pays what it holds in proportion and its policies end.
A holder buys cover when it could not bear the worst year from its own cash and the premium is less than that loss.
Insurers are agents with a purse in the book, so any actor may found one.
"""
from typing import Dict, List, Optional

from . import ownership
from .capital_state import CapitalState, Hazard, Insurer, Policy
from .types import AgentId, Transfer

EPSILON = 1e-9
PREMIUM_PURPOSE = "insurance premium"
CLAIM_PURPOSE = "insurance claim"
ASSESSMENT_PURPOSE = "mutual assessment"
INSURANCE_UNDERWRITING = "insurance_underwriting"     # the institution a society must hold for a company to sell cover
RISK_POOLING = "risk_pooling"                         # the institution a society must hold for members to insure one another
HARVEST = "harvest"                                   # the hazard of a poor growing year, read from the year's weather


def loss_share_of(factor: float) -> float:
    """The share of a normal harvest a year's weather factor took: nothing at or above normal."""
    return min(1.0, max(0.0, 1.0 - factor))


def observe(state: CapitalState, hazard_id: str, loss_share: float) -> None:
    """A year of the hazard is watched: the share it took joins the record."""
    hazard = state.hazards.setdefault(hazard_id, Hazard())
    hazard.years += 1
    hazard.loss_share_total += loss_share
    hazard.worst = max(hazard.worst, loss_share)


def expected_loss_share(state: CapitalState, hazard_id: str) -> Optional[float]:
    """The mean share of the value exposed that the hazard takes a year, from the years watched; None with no record."""
    hazard = state.hazards.get(hazard_id)
    if hazard is None or hazard.years <= 0:
        return None
    return hazard.loss_share_total / hazard.years


def premium_rate(state: CapitalState, hazard_id: str, market_rate: float) -> Optional[float]:
    """What a company charges per unit insured: the expected claims, and the return on the capital it holds for the
    worst year beyond them. None with no record of the hazard."""
    expected = expected_loss_share(state, hazard_id)
    if expected is None:
        return None
    return expected + max(0.0, market_rate) * max(0.0, state.hazards[hazard_id].worst - expected)


def wants_cover(cash: float, insured_value: float, rate: Optional[float], state: CapitalState, hazard_id: str) -> bool:
    """A holder buys cover when its own cash would not bear the worst year seen and the cover costs less than that
    year's loss."""
    if rate is None or insured_value <= EPSILON or hazard_id not in state.hazards:
        return False
    worst_loss = state.hazards[hazard_id].worst * insured_value
    return worst_loss > cash and rate * insured_value < worst_loss


def found(record, founder: AgentId, capital: float, year: int, money: str, mutual: bool = False) -> Optional[Insurer]:
    """A company, with `capital` of the founder's cash in its purse (none if the founder holds less); or a mutual,
    which holds no capital and is formed by its members."""
    state = record.capital
    insurer_id = "insurer:%d" % len(state.insurers)
    if mutual:
        insurer = Insurer(insurer_id, founder, year, mutual=True)
    else:
        capital = min(capital, record.book.balance(founder, money))
        if capital <= 0.0:
            return None
        insurer = Insurer(insurer_id, founder, year, paid_in=capital)
        record.book.transfer(Transfer(founder, insurer_id, money, capital, "insurer capital"))
    state.insurers[insurer_id] = insurer
    return insurer


def standing(state: CapitalState, mutual: bool = False) -> List[Insurer]:
    return [insurer for _id, insurer in sorted(state.insurers.items()) if insurer.failed_year < 0 and insurer.mutual == mutual]


def insure(state: CapitalState, insurer_id: str, holder: AgentId, hazard_id: str, insured_value: float) -> Policy:
    """The holder is covered for `insured_value` against the hazard; one policy per holder and hazard with the insurer."""
    for policy in state.policies:
        if policy.insurer == insurer_id and policy.holder == holder and policy.hazard == hazard_id:
            policy.insured_value = insured_value
            return policy
    policy = Policy(insurer_id, holder, hazard_id, insured_value)
    state.policies.append(policy)
    return policy


def policies_of(state: CapitalState, insurer_id: str, hazard_id: Optional[str] = None) -> List[Policy]:
    return [policy for policy in state.policies if policy.insurer == insurer_id and (hazard_id is None or policy.hazard == hazard_id)]


def collect_premiums(record, money: str, market_rate: float) -> Dict[AgentId, float]:
    """Each holder of a company's policy pays the premium for the year, from its cash (a holder who cannot pay is
    dropped). What each paid."""
    state = record.capital
    paid: Dict[AgentId, float] = {}
    kept: List[Policy] = []
    for policy in state.policies:
        insurer = state.insurers.get(policy.insurer)
        if insurer is None or insurer.mutual or insurer.failed_year >= 0:
            kept.append(policy)
            continue
        rate = premium_rate(state, policy.hazard, market_rate)
        premium = 0.0 if rate is None else rate * policy.insured_value
        if premium <= EPSILON:
            kept.append(policy)
            continue
        if record.book.balance(policy.holder, money) + EPSILON < premium:
            continue
        record.book.transfer(Transfer(policy.holder, policy.insurer, money, premium, PREMIUM_PURPOSE))
        paid[policy.holder] = paid.get(policy.holder, 0.0) + premium
        kept.append(policy)
    state.policies = kept
    return paid


def settle(record, money: str, hazard_id: str, loss_share: float, year: int) -> Dict[AgentId, float]:
    """The hazard took `loss_share` of the value exposed: every insurer pays its policies' claims, a company from its
    purse and a mutual from its members' cash; one that cannot pays in proportion and, if a company, fails. What each
    claimant received. The year joins the hazard's record afterwards (`observe`), so this year's loss is not in the
    premium that bought the cover."""
    state = record.capital
    received: Dict[AgentId, float] = {}
    if loss_share > EPSILON:
        for insurer_id in sorted(state.insurers):
            insurer = state.insurers[insurer_id]
            if insurer.failed_year >= 0:
                continue
            claims = {policy.holder: loss_share * policy.insured_value for policy in policies_of(state, insurer_id, hazard_id)}
            paid = _pay_mutual(record, insurer, claims, money) if insurer.mutual else _pay_company(record, insurer, claims, money, year)
            for holder, amount in paid.items():
                received[holder] = received.get(holder, 0.0) + amount
    observe(state, hazard_id, loss_share)
    return received


def _pay_company(record, insurer: Insurer, claims: Dict[AgentId, float], money: str, year: int) -> Dict[AgentId, float]:
    total = sum(claims.values())
    cash = max(0.0, record.book.balance(insurer.agent_id, money))
    if total <= EPSILON:
        return {}
    share = min(1.0, cash / total)
    payments = [Transfer(insurer.agent_id, holder, money, claim * share, CLAIM_PURPOSE) for holder, claim in sorted(claims.items())]
    record.book.transfer_many(payments)
    if share < 1.0 - EPSILON:
        insurer.failed_year = year
        record.capital.policies = [policy for policy in record.capital.policies if policy.insurer != insurer.agent_id]
    return {payment.payee: payment.amount for payment in payments}


def _pay_mutual(record, insurer: Insurer, claims: Dict[AgentId, float], money: str) -> Dict[AgentId, float]:
    """The members pay the claims between them, each in proportion to what it insured, as far as its cash goes; the
    claimants are paid in proportion to what was collected."""
    total = sum(claims.values())
    if total <= EPSILON:
        return {}
    insured = {policy.holder: policy.insured_value for policy in policies_of(record.capital, insurer.agent_id)}
    insured_total = sum(insured.values())
    calls = {member: min(max(0.0, record.book.balance(member, money)), total * value / insured_total)
             for member, value in sorted(insured.items())}
    collected = sum(calls.values())
    pot = insurer.agent_id
    record.book.transfer_many([Transfer(member, pot, money, call, ASSESSMENT_PURPOSE) for member, call in calls.items() if call > EPSILON])
    share = min(1.0, collected / total)
    payments = [Transfer(pot, holder, money, claim * share, CLAIM_PURPOSE) for holder, claim in sorted(claims.items())]
    record.book.transfer_many(payments)
    return {payment.payee: payment.amount for payment in payments}


def pay_founder(record, insurer: Insurer, money: str, required: float) -> float:
    """What a standing company holds beyond its founder's capital and the `required` capital goes back to its
    founder as a dividend; the amount."""
    if insurer.mutual or insurer.failed_year >= 0:
        return 0.0
    surplus = record.book.balance(insurer.agent_id, money) - max(insurer.paid_in, required)
    if surplus <= EPSILON:
        return 0.0
    record.book.transfer_many(ownership.spread(record, [Transfer(insurer.agent_id, insurer.founder, money, surplus, "dividend")]))
    return surplus


def required_capital(state: CapitalState, insurer_id: str) -> float:
    """The capital a company holds for the worst year seen of the hazards it covers, over what it insured."""
    return sum(state.hazards[policy.hazard].worst * policy.insured_value for policy in policies_of(state, insurer_id)
               if policy.hazard in state.hazards)
