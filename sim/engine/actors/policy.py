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


POLICY_FACTORIES: Dict[str, Callable[[], Policy]] = {
	"value": ValuePolicy,
	"idle": IdlePolicy,
}


def register_policy(kind: str, factory: Callable[[], Policy]) -> None:
	"""Make a policy nameable from a save file or a mod."""
	POLICY_FACTORIES[kind] = factory


def make_policy(kind: str) -> Policy:
	return POLICY_FACTORIES.get(kind, ValuePolicy)()
