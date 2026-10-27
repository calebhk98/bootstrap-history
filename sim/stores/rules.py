"""Declared stores: a named value per tile, per actor or per ordered pair of actors.

A store is declared in data (`data/world/stores.json` for the base game, `data/stores.json` in a mod) or by a mod's code
through `api.store`; a mod's names are `<mod_id>:<name>`, and a name is declared once across the base game and every mod.
Only values that differ from the default are kept."""
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Sequence

from sim.mod_errors import ModError

TILE, ACTOR, ACTOR_PAIR = "tile", "actor", "actor_pair"
KEYED_BY = (TILE, ACTOR, ACTOR_PAIR)
PAIR_SEPARATOR = "|"


@dataclass(frozen=True)
class StoreSpec:
    name: str
    owner: str          # the declaring mod's id; empty for the base game
    keyed_by: str
    default: Any
    unit: str


def check_spec(spec: StoreSpec, where: str) -> None:
    if spec.keyed_by not in KEYED_BY:
        raise ModError("%s: store %s is keyed_by %r; it must be one of %s" % (where, spec.name, spec.keyed_by, ", ".join(KEYED_BY)))
    try:
        json.dumps(spec.default)
    except TypeError:
        raise ModError("%s: store %s has a default that is not JSON data" % (where, spec.name))


def declare_all(answers: Sequence[Iterable[StoreSpec]]) -> Dict[str, StoreSpec]:
    """The stores of one game, from every provider's declarations in provider order; a name declared twice by different
    owners is an error naming both."""
    declared: Dict[str, StoreSpec] = {}
    for answer in answers:
        for spec in answer:
            check_spec(spec, spec.owner and "mod %s" % spec.owner or "the base game")
            held = declared.get(spec.name)
            if held is not None:
                if held == spec:
                    continue
                raise ModError("%s: store %s is already declared by %s" % (
                    spec.owner and "mod %s" % spec.owner or "the base game", spec.name, held.owner or "the base game"))
            declared[spec.name] = spec
    return declared


def store_key(spec: StoreSpec, key: Any) -> str:
    """The saved form of a key: a tile or actor id as is, a pair as `first|second` (order matters)."""
    if spec.keyed_by == ACTOR_PAIR:
        if not (isinstance(key, (tuple, list)) and len(key) == 2) and not (isinstance(key, str) and key.count(PAIR_SEPARATOR) == 1):
            raise ModError("store %s is keyed by an ordered pair of actors, not %r" % (spec.name, key))
        key = PAIR_SEPARATOR.join(key) if not isinstance(key, str) else key
    if not isinstance(key, str) or not key:
        raise ModError("store %s is keyed by %s ids (text), not %r" % (spec.name, spec.keyed_by, key))
    return key
