"""Which goods substitute for which: goods that serve the same household need, from the need data's `goods` table."""
from typing import Any, Dict, FrozenSet, Mapping


def needs_served(goods: Mapping[str, Any]) -> Dict[str, FrozenSet[str]]:
	"""material -> the needs it serves, from the need data's goods ({material: {"satisfies": {need: effectiveness}}})."""
	return {material: frozenset(attributes.get("satisfies") or {}) for material, attributes in goods.items()}


def serving(served: Mapping[str, FrozenSet[str]], need_id: str) -> FrozenSet[str]:
	"""The materials that serve one need."""
	return frozenset(material for material, needs in served.items() if need_id in needs)


def substitutes_of(served: Mapping[str, FrozenSet[str]], material: str) -> FrozenSet[str]:
	"""The materials that serve a need `material` serves (none for a material no need names)."""
	needs = served.get(material, frozenset())
	return frozenset(other for other, other_needs in served.items() if other != material and needs & other_needs)


def serves_a_need(served: Mapping[str, FrozenSet[str]], material: str) -> bool:
	"""Whether the needs data names this material as serving some household need."""
	return bool(served.get(material))
