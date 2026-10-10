"""Decision policies: who chooses for an actor.

An actor gathers the options open to it and hands them to its policy; the
policy returns the ones to act on. A human player, an AI or a mod can drive
any actor by supplying a different policy.
"""
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List


@dataclass(frozen=True)
class Option:
	"""One thing an actor could do, priced in its own money."""
	subject: str
	worth: float
	cost: float
	chance: float = 1.0
	detail: Any = None

	@property
	def net(self) -> float:
		return self.worth * self.chance - self.cost


@dataclass(frozen=True)
class Decision:
	"""A question put to a policy: pick from `options` within `budget`."""
	kind: str
	options: List[Option]
	budget: float


class Policy:
	"""Interface: return the chosen subset of a decision's options."""

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		raise NotImplementedError


class ValuePolicy(Policy):
	"""Best net value first, while the budget lasts; nothing at a loss."""

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		chosen: List[Option] = []
		remaining = decision.budget
		for option in sorted(decision.options, key=lambda item: (-item.net, item.subject)):
			if option.net <= 0 or option.cost > remaining:
				continue
			chosen.append(option)
			remaining -= option.cost
		return chosen


class CallbackPolicy(Policy):
	"""Delegates to a function returning the subjects to act on.

	The hook for a human player or a mod: the function sees the actor and
	the decision, and anything it names that is not on offer is ignored.
	"""

	def __init__(self, decide: Callable[[Any, Decision], Iterable[str]]) -> None:
		self._decide = decide

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		wanted = set(self._decide(actor, decision) or ())
		return [option for option in decision.options if option.subject in wanted]


class IdlePolicy(Policy):
	"""Never acts; decisions arrive some other way (the founder's commands)."""

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		return []


EXPORT_DECISION = "export"


class ExportPolicy(ValuePolicy):
	"""A state's answer to selling goods abroad: it keeps back what it holds as a state monopoly (its
	record's `state_monopolies`, set at the start by its country's data and changeable like any record
	field) and sells what pays. Any other decision is taken as ValuePolicy takes it."""

	def choose(self, actor: Any, decision: Decision) -> List[Option]:
		if decision.kind != EXPORT_DECISION:
			return super().choose(actor, decision)
		kept_back = getattr(getattr(actor, "record", None), "state_monopolies", None) or ()
		offered = [option for option in decision.options if option.subject not in kept_back]
		return super().choose(actor, Decision(decision.kind, offered, decision.budget))


def exports_allowed(actor: Any, materials: Iterable[str]) -> List[str]:
	"""The materials, sorted, that the actor's state will sell abroad: it is asked, as an export decision,
	through its own policy. Each sale is worth something and costs nothing, so only a policy that holds
	a good back keeps it from leaving."""
	decision = Decision(EXPORT_DECISION, [Option(subject=material, worth=1.0, cost=0.0)
										  for material in sorted(set(materials))], float("inf"))
	policy = getattr(actor, "decision_policy", None) or ExportPolicy()
	return sorted(option.subject for option in policy.choose(actor, decision))


POLICY_FACTORIES: Dict[str, Callable[[], Policy]] = {
	"value": ValuePolicy,
	"idle": IdlePolicy,
	"export": ExportPolicy,
}


def register_policy(kind: str, factory: Callable[[], Policy]) -> None:
	"""Make a policy nameable from a save file or a mod."""
	POLICY_FACTORIES[kind] = factory


def make_policy(kind: str) -> Policy:
	return POLICY_FACTORIES.get(kind, ValuePolicy)()
