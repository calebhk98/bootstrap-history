"""Shared mod types plus field-claim and removal-claim bookkeeping."""
import copy
from dataclasses import MISSING, dataclass, field, fields
from typing import Any, Dict, List


class ModError(ValueError):
    """A mod cannot be loaded without making an ambiguous choice."""


@dataclass(frozen=True)
class ModManifest:
    id: str
    name: str
    version: str
    dependencies: List[str]
    conflicts: List[str]
    directory: str = field(repr=False, compare=False, default="")
    min_game_version: str = ""
    # Version range a dependency must satisfy, by dependency id; absent means any version.
    dependency_ranges: Dict[str, str] = field(default_factory=dict, compare=False)


# Required manifest keys are the manifest type's fields without a default.
MANIFEST_KEYS = tuple(item.name for item in fields(ModManifest)
                      if item.default is MISSING and item.default_factory is MISSING)

# Patch keys that steer the loader and are never merged into content.
CONTROL_KEYS = ("override", "replaces", "remove")
REMOVED = "<removed>"


def deep_merge(base: Dict[str, Any], patch: Dict[str, Any], nested: bool = False) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if key in CONTROL_KEYS:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value, nested=True)
        elif value is None and nested and key in result:
            # null inside a nested map deletes that key from the base map
            del result[key]
        else:
            result[key] = copy.deepcopy(value)
    return result


def ancestors(manifest: ModManifest, by_id: Dict[str, ModManifest]) -> set:
    """Every mod this one depends on, directly or transitively."""
    found: set = set()
    pending = list(manifest.dependencies)
    while pending:
        mod_id = pending.pop()
        if mod_id not in found:
            found.add(mod_id)
            pending.extend(by_id[mod_id].dependencies if mod_id in by_id else [])
    return found


def unrelated(earlier: str, manifest: ModManifest, by_id: Dict[str, ModManifest]) -> bool:
    return bool(earlier) and earlier != manifest.id and earlier not in ancestors(manifest, by_id)


def check_not_removed(claims: Dict[Any, str], kind: str, item_id: str,
                      manifest: ModManifest, by_id: Dict[str, ModManifest]) -> None:
    """Patching what an unrelated mod removed is a conflict naming both."""
    remover = claims.get((kind, item_id, REMOVED))
    if unrelated(remover, manifest, by_id):
        raise ModError("mod %s removes %s %s but mod %s patches it; make one depend on the "
                       "other to choose a winner" % (remover, kind, item_id, manifest.id))


def claim_fields(claims: Dict[Any, str], kind: str, item_id: str, patch: Dict[str, Any],
                 manifest: ModManifest, by_id: Dict[str, ModManifest]) -> None:
    """Record which mod set each field; two unrelated mods on one field is an error."""
    check_not_removed(claims, kind, item_id, manifest, by_id)
    for name in patch:
        if name in CONTROL_KEYS or name == "id":
            continue
        earlier = claims.get((kind, item_id, name))
        if unrelated(earlier, manifest, by_id):
            raise ModError("mods %s and %s both override field %r of %s %s; make one depend on "
                           "the other to choose a winner" % (earlier, manifest.id, name, kind, item_id))
        claims[(kind, item_id, name)] = manifest.id


def claim_removal(claims: Dict[Any, str], kind: str, item_id: str,
                  manifest: ModManifest, by_id: Dict[str, ModManifest]) -> None:
    """Removing what an unrelated mod already patched is a conflict naming both."""
    for (claimed_kind, claimed_id, name), earlier in claims.items():
        if (claimed_kind, claimed_id) == (kind, item_id) and unrelated(earlier, manifest, by_id):
            raise ModError("mod %s patches %s %s but mod %s removes it; make one depend on the "
                           "other to choose a winner" % (earlier, kind, item_id, manifest.id))
    claims[(kind, item_id, REMOVED)] = manifest.id


def removed_by(claims: Dict[Any, str], kind: str) -> Dict[str, str]:
    """Ids of this kind that were removed, mapped to the removing mod."""
    return {item_id: mod for (claimed_kind, item_id, name), mod in claims.items()
            if claimed_kind == kind and name == REMOVED}
