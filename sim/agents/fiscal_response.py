"""How a state meets a shortfall: a menu of responses, each with its consequences, and policies that choose.

A state whose standing need exceeds its purse is put one decision, `fiscal_response`. Its options are the ways to
cover the gap: borrow, cut lines, defer pay as arrears, debase the coin, levy the taxpayers it can see, demand
more in kind, raise the rate of a form it collects in coin. Each option states how much of the gap it can cover and what it does to others, per share of the
need covered (`consequences`): interest paid, services lost, the share of pay left unpaid (which lowers the army's
loyalty), coin metal cut (which raises prices), income taken from taxpayers. The state's decision policy chooses.
A player state (a `CallbackPolicy` naming responses) and an AI state (a `FiscalPolicy` valuing consequences)
face the same menu; no policy is the engine's rule. What a policy leaves uncovered is cut, as lines unpaid with
nothing set against them cannot be paid.
"""
import dataclasses
from typing import Any, Dict, Iterable, List, Optional, Sequence

from . import arrears, evasion
from .policy import CallbackPolicy, Decision, IdlePolicy, Option, Policy, register_policy
from .tuning import LEVY_RATE_CEILING
from .tuning_coinage import COIN_RESTRIKE_SHARE_PER_YEAR, DEBASEMENT_SHARE_CEILING
from .tuning_fiscal import (FISCAL_BURDEN_WEIGHT, FISCAL_DEBT_CARRY_YEARS, FISCAL_LOYALTY_WEIGHT,
							FISCAL_PRICE_RISE_WEIGHT, FISCAL_SERVICE_LOSS_WEIGHT, KIND_DEMAND_RATE_STEP, RATE_RAISE_STEP)

FISCAL_DECISION = "fiscal_response"
BORROW, CUT, ARREARS, DEBASE, LEVY, KIND, RATE = ("borrow", "cut_lines", "arrears", "debase", "levy", "demand_in_kind",
												  "raise_rate")
RESPONSES = (BORROW, CUT, ARREARS, DEBASE, LEVY, KIND, RATE)
STRUCK_COIN = "struck_coin"
_TINY = 1e-12


def _option(subject: str, capacity: float, consequences: Dict[str, float]) -> Option:
	"""`worth` is the money of shortfall the response can cover; `detail` its consequences per share of the need covered."""
	return Option(subject=subject, worth=max(0.0, capacity), cost=0.0, detail=consequences)


def menu(government: Any, world: Any, lines: Sequence[Any], gap: float) -> Decision:
	"""The responses open to `government` to cover `gap` of the money the standing `lines` need."""
	need = sum(line.money for line in lines)
	pay_need = sum(line.money for line in lines if line.name in arrears.PAY_LINES)
	rate = world.market_rate()
	options = [_option(CUT, gap, {"services_lost": 1.0})]
	ceiling = government.credit_ceiling(world)
	if ceiling > 0.0:
		borrowed = min(gap, ceiling)
		options.append(_option(BORROW, borrowed, {"interest": government.rate_on_loan(world, borrowed)}))
	carry = {"interest": rate, "unpaid_pay": need / pay_need if pay_need > 0.0 else 0.0}
	if pay_need > 0.0:
		options.append(_option(ARREARS, min(gap, pay_need), dict(carry)))
	struck_again = world.coin_stock_value() * COIN_RESTRIKE_SHARE_PER_YEAR if world.coin_regime() == STRUCK_COIN else 0.0
	if struck_again > 0.0:
		options.append(_option(DEBASE, struck_again * DEBASEMENT_SHARE_CEILING, dict(carry, coin_cut=need / struck_again)))
	visible = sum(world.notice_over(scale) * income for scale, income in world.visible_taxpayers())
	if visible > 0.0:
		options.append(_option(LEVY, visible * LEVY_RATE_CEILING, dict(carry, income_taken=need / visible)))
	kind_base = in_kind_base(government.record, world)
	if kind_base > 0.0:
		options.append(_option(KIND, kind_base * KIND_DEMAND_RATE_STEP, dict(carry, income_taken=need / kind_base)))
	coin_base = coin_rate_base(world)
	if coin_base > 0.0:
		options.append(_option(RATE, rate_raise_yield(world), dict(carry, income_taken=need / coin_base)))
	return Decision(FISCAL_DECISION, options, gap)


def raisable_coin_forms(world: Any) -> List[Any]:
	"""The assessments of the forms the state collects in coin on a base of money, at a rate above nothing: the
	forms whose rate it can raise for money (not a labour due, not a form paid in kind)."""
	return [assessed for assessed in world.revenue_assessments()
			if not assessed.in_kind and not assessed.in_labour and assessed.rate > 0.0 and assessed.base > 0.0]


def coin_rate_base(world: Any) -> float:
	"""Money's worth of the base the state's coin forms are assessed on."""
	return sum(assessed.base * assessed.collectible for assessed in raisable_coin_forms(world))


def new_rate_of(rate: float) -> float:
	"""The rate a form is raised to in one full step."""
	return min(1.0, rate * (1.0 + RATE_RAISE_STEP))


def rate_raise_yield(world: Any) -> float:
	"""Money the state's coin forms yield more, next year, at a full step of rate: the extra rate on the base the
	payers still declare at that rate. A form on what actors hold loses to hiding as the rate climbs (evasion.py),
	so it yields less than the rate times the base."""
	extra = 0.0
	for assessed in raisable_coin_forms(world):
		raised = new_rate_of(assessed.rate)
		if assessed.payers:
			gross = assessed.base + assessed.concealed
			extra += (evasion.yield_of_rate(gross, raised, assessed.collectible)
					  - evasion.yield_of_rate(gross, assessed.rate, assessed.collectible))
		else:
			extra += assessed.collectible * (raised - assessed.rate) * assessed.base
	return max(0.0, extra)


def in_kind_base(record: Any, world: Any) -> float:
	"""Money's worth of the base the state's forms paid in kind were assessed on last year."""
	base = 0.0
	for form in world.revenue_forms():
		taken = record.revenue_in_kind.get(form["form"], 0.0)
		if form.get("paid_in") and form["rate"] > 0.0:
			base += taken / form["rate"]
	return base


def fill(order: Iterable[str], options: Sequence[Option], gap: float) -> Dict[str, float]:
	"""Money of `gap` covered by each response named in `order`, taking each to its capacity in turn; whatever is
	left is cut."""
	by_name = {option.subject: option for option in options}
	covered: Dict[str, float] = {}
	left = gap
	for name in order:
		option = by_name.get(name)
		if name == CUT:
			break   # what a state would rather cut than cover any other way is cut
		if option is None or name in covered:
			continue
		covered[name] = min(left, option.worth)
		left -= covered[name]
	if left > _TINY:
		covered[CUT] = left
	return {name: amount for name, amount in covered.items() if amount > _TINY}


class FiscalPolicy(Policy):
	"""An AI state's answer: values each response by its consequences and covers the gap with the cheapest first."""

	def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
		self.weights = dict(DEFAULT_WEIGHTS, **(weights or {}))

	def unit_cost(self, option: Option) -> float:
		return sum(self.weights.get(name, 0.0) * amount for name, amount in (option.detail or {}).items())

	def order(self, options: Sequence[Option]) -> List[str]:
		return [option.subject for option in sorted(options, key=lambda item: (self.unit_cost(item), item.subject))]

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		covered = fill(self.order(decision.options), decision.options, decision.budget)
		return [dataclasses.replace(option, worth=covered[option.subject])
				for option in decision.options if option.subject in covered]


DEFAULT_WEIGHTS = {"interest": FISCAL_DEBT_CARRY_YEARS, "services_lost": FISCAL_SERVICE_LOSS_WEIGHT,
				   "unpaid_pay": FISCAL_LOYALTY_WEIGHT, "coin_cut": FISCAL_PRICE_RISE_WEIGHT,
				   "income_taken": FISCAL_BURDEN_WEIGHT}


class OrderedFiscalPolicy(FiscalPolicy):
	"""A state that works down a fixed list of responses whatever they cost."""

	def __init__(self, order: Sequence[str]) -> None:
		super().__init__()
		self.fixed_order = tuple(order)

	def order(self, options: Sequence[Option]) -> List[str]:
		return list(self.fixed_order)


# the order of the old engine rule, kept as one policy among others: borrow, debase, levy, defer pay, cut
CASCADE_ORDER = (BORROW, DEBASE, LEVY, ARREARS, CUT)
LEVY_FIRST_ORDER = (BORROW, LEVY, KIND, RATE, ARREARS, CUT)
register_policy("fiscal_consequence", FiscalPolicy)
register_policy("fiscal_levy_first", lambda: OrderedFiscalPolicy(LEVY_FIRST_ORDER))
register_policy("fiscal_cascade", lambda: OrderedFiscalPolicy(CASCADE_ORDER))
register_policy("fiscal_austere", lambda: FiscalPolicy({"interest": 10.0 * FISCAL_DEBT_CARRY_YEARS,
														"coin_cut": 10.0 * FISCAL_PRICE_RISE_WEIGHT,
														"income_taken": 10.0 * FISCAL_BURDEN_WEIGHT,
														"services_lost": 0.01 * FISCAL_SERVICE_LOSS_WEIGHT}))


def respond(government: Any, world: Any, lines: Sequence[Any], gap: float) -> Dict[str, float]:
	"""Money of `gap` covered by each response, as `government`'s decision policy chooses from the menu. A
	policy that returns an allocation (a `FiscalPolicy`) is taken at its amounts; one that only names responses (a
	player's `CallbackPolicy`) has them covered in the menu's order; any other policy leaves the choice to the
	state's consequence valuation."""
	if gap <= _TINY:
		return {}
	decision = menu(government, world, lines, gap)
	policy = getattr(government, "decision_policy", None)
	if isinstance(policy, FiscalPolicy):
		return {option.subject: option.worth for option in policy.choose(government, decision)}
	if isinstance(policy, CallbackPolicy):
		named = [option.subject for option in policy.choose(government, decision)]
		return fill(named, decision.options, gap)
	if isinstance(policy, IdlePolicy):
		return fill([], decision.options, gap)
	return {option.subject: option.worth for option in FiscalPolicy().choose(government, decision)}
