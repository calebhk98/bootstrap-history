"""The land module's map views as plain values for a module under test, answered by a real `Land` over a map.

    views = land_views.of(civilisation, ("tiles_listed_by", "carriage_facts"))              # the base map
    views = land_views.of(civilisation, ("carriage_facts",), world_map=small_map)           # a map the test builds

so a module's test reads what the land module gives, not a stand-in that answers whatever it is asked."""
from typing import Any, Dict, Iterable, Optional

from sim.tests import land_host


def of(civilisation: Dict[str, Any], names: Iterable[str], world_map: Optional[Any] = None, held_techniques: Any = frozenset()) -> Dict[str, Any]:
	"""{view name: the land module's answer} for each of `names`; `world_map` replaces the base map the module opens."""
	module = land_host.build(civilisation, views={"held_techniques": lambda include_starting=False: held_techniques})
	if world_map is not None:
		module._map_cache = world_map
	return {name: getattr(module, name) for name in names}
