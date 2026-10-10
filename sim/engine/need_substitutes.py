"""Which goods substitute for which: goods that serve the same household need (data/world/needs.json and mods)."""
import os
from typing import Dict, FrozenSet

from . import need_data
from .mods import get_ordered_mods

_REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# the installed mods -> material -> the needs it serves
_NEEDS_BY_MODS: Dict[tuple, Dict[str, FrozenSet[str]]] = {}


def _needs_served() -> Dict[str, FrozenSet[str]]:
	"""material -> the needs it serves, for the installed content (built once per set of mods)."""
	mods = tuple(manifest.id for manifest in get_ordered_mods(os.path.join(_REPOSITORY_ROOT, "mods")))
	built = _NEEDS_BY_MODS.get(mods)
	if built is None:
		goods = need_data.load_needs(_REPOSITORY_ROOT)["goods"]
		built = _NEEDS_BY_MODS[mods] = {material: frozenset(attributes.get("satisfies") or {})
										for material, attributes in goods.items()}
	return built


def serving(need_id: str) -> FrozenSet[str]:
	"""The materials that serve one need."""
	return frozenset(material for material, needs in _needs_served().items() if need_id in needs)


def substitutes_of(material: str) -> FrozenSet[str]:
	"""The materials that serve a need `material` serves (none for a material no need names)."""
	served = _needs_served()
	needs = served.get(material, frozenset())
	return frozenset(other for other, other_needs in served.items() if other != material and needs & other_needs)
