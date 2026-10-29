"""Mod goal entries: added, removed, or patched by their `node`."""
from typing import Any, Dict, List

from .mods_base import (ModError, ModManifest, check_not_removed, claim_fields, claim_removal,
                        deep_merge)
from .mods_remove import GOAL


def apply_goal_entries(goals: List[Dict[str, Any]], entries: List[Dict[str, Any]],
                       nodes: Dict[str, Any], path: str, claims: Dict[Any, str],
                       manifest: ModManifest, by_id: Dict[str, ModManifest]) -> List[Dict[str, Any]]:
    """Goal list after one mod's goals.json entries; a goal is identified by its node."""
    goals = list(goals)
    for entry in entries:
        node_id = entry.get("node")
        position = next((i for i, goal in enumerate(goals) if goal.get("node") == node_id), None)
        if entry.get("remove") is True:
            if position is None:
                raise ModError("%s removes missing goal for node %r" % (path, node_id))
            claim_removal(claims, GOAL, node_id, manifest, by_id)
            del goals[position]
        elif entry.get("override") is True:
            check_not_removed(claims, GOAL, node_id, manifest, by_id)
            if position is None:
                raise ModError("mod %s: %s overrides missing goal for node %r" %
                               (manifest.id, path, node_id))
            # `node` identifies the goal; only the other fields are claimed
            claim_fields(claims, GOAL, node_id,
                         {key: value for key, value in entry.items() if key != "node"},
                         manifest, by_id)
            goals[position] = deep_merge(goals[position], entry)
        elif node_id not in nodes:
            raise ModError("%s names missing goal node %r" % (path, node_id))
        else:
            goals.append(entry)
    return goals
