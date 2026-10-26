"""One seat hears of what another has built, as an onlooker would: by what can be seen of it from its place.

Under fog a seat sees what it has built, what it has revealed and what it could begin next. Another seat's work
becomes known to it only when enough of it shows at the observer's distance (the same visibility an actor
copying from sight gets, visibility.py); a secret shows little, a published invention shows widely."""
from typing import Any, Callable, Mapping, Set

from sim.agents.api import OBSERVATION_RANGE_KM, PLAYER_VISIBLE_EXPOSURE, SECRET_EXPOSURE

from .visibility import base_visibility, seen_from


def nodes_heard_of(builder: Any, builder_disclosures: Mapping[str, Any], observer: Any,
                   distance_km: float, copy_difficulty: Callable[[str], float]) -> Set[str]:
    """The nodes `builder` (a seat's projects) made (and chose `builder_disclosures` for) that `observer` has not got
    or heard of and can see enough of from `distance_km`."""
    heard = set()
    for node_id in builder.done - builder.granted - observer.done - observer.revealed:
        mode = (builder_disclosures.get(node_id) or {}).get("mode", "default")
        visibility = base_visibility(mode, node_id in builder.operating, copy_difficulty(node_id), SECRET_EXPOSURE)
        if seen_from(visibility, distance_km, OBSERVATION_RANGE_KM) >= PLAYER_VISIBLE_EXPOSURE:
            heard.add(node_id)
    return heard
