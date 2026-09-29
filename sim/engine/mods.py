"""Discovery, ordering, and data overlays for third-party mods."""
import copy
import json
import os
import re
from typing import Any, Dict, Iterable, List

from .mods_base import (CONTROL_KEYS, ModError, ModManifest, check_not_removed, claim_fields,
                        claim_removal, removed_by)
from .mods_remove import (GOAL, RECIPE, TECH, check_recipe_references, check_tree_references)


def _manifest(path: str) -> ModManifest:
    with open(path, encoding="utf-8") as source:
        raw = json.load(source)
    required = ("id", "name", "version", "dependencies", "conflicts")
    missing = [name for name in required if name not in raw]
    if missing:
        raise ModError("%s is missing manifest fields: %s" % (path, ", ".join(missing)))
    mod_id = raw["id"]
    if not isinstance(mod_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", mod_id):
        raise ModError("%s has invalid mod id %r" % (path, mod_id))
    for key in ("dependencies", "conflicts"):
        if not isinstance(raw[key], list) or not all(isinstance(item, str) for item in raw[key]):
            raise ModError("%s field %s must be a list of mod ids" % (path, key))
    return ModManifest(mod_id, str(raw["name"]), str(raw["version"]),
                       list(raw["dependencies"]), list(raw["conflicts"]),
                       os.path.dirname(path))


def get_ordered_mods(mods_dir: str) -> List[ModManifest]:
    """Return installed mods in stable dependency order."""
    if not os.path.isdir(mods_dir):
        return []
    manifests: Dict[str, ModManifest] = {}
    for folder in sorted(os.listdir(mods_dir)):
        manifest_path = os.path.join(mods_dir, folder, "mod.json")
        if not os.path.isfile(manifest_path):
            continue
        manifest = _manifest(manifest_path)
        if manifest.id in manifests:
            raise ModError("mod id %s is declared by both %s and %s" %
                           (manifest.id, manifests[manifest.id].directory, manifest.directory))
        manifests[manifest.id] = manifest
    for manifest in manifests.values():
        missing = sorted(set(manifest.dependencies) - set(manifests))
        if missing:
            raise ModError("mod %s requires missing mods: %s" % (manifest.id, ", ".join(missing)))
        conflicts = sorted(set(manifest.conflicts) & set(manifests))
        if conflicts:
            raise ModError("mod %s conflicts with installed mods: %s" %
                           (manifest.id, ", ".join(conflicts)))

    ordered: List[ModManifest] = []
    visiting, visited = set(), set()

    def visit(mod_id: str) -> None:
        if mod_id in visiting:
            raise ModError("mod dependency cycle includes %s" % mod_id)
        if mod_id in visited:
            return
        visiting.add(mod_id)
        for dependency in sorted(manifests[mod_id].dependencies):
            visit(dependency)
        visiting.remove(mod_id)
        visited.add(mod_id)
        ordered.append(manifests[mod_id])

    for mod_id in sorted(manifests):
        visit(mod_id)
    return ordered


def _json_files(directory: str) -> Iterable[str]:
    if os.path.isdir(directory):
        for filename in sorted(os.listdir(directory)):
            if filename.endswith(".json"):
                yield os.path.join(directory, filename)


def _deep_merge(base: Dict[str, Any], patch: Dict[str, Any], nested: bool = False) -> Dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if key in CONTROL_KEYS:
            continue
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value, nested=True)
        elif value is None and nested and key in result:
            # null inside a nested map deletes that key from the base map
            del result[key]
        else:
            result[key] = copy.deepcopy(value)
    return result


def _check_new_id(manifest: ModManifest, item_id: str, override: bool, path: str) -> None:
    if not override and not item_id.startswith(manifest.id + "_"):
        raise ModError("%s introduces un-prefixed id %r; expected %s_* or override=true" %
                       (path, item_id, manifest.id))


def _node_defaults(node: Dict[str, Any]) -> Dict[str, Any]:
    defaults = {"ph": 60, "lab": {}, "mat": {}, "cap": 200, "up": 40,
                "risk": 0.15, "rev": 0, "sch": 0, "art": 1, "conf": "C",
                "kb": "", "pre": [], "req_any": [], "traits": [],
                "build_yrs": 0.0, "adopt_yrs": 0.0, "sus": 0, "gov": 0,
                "dev_years": None, "dev_people": None}
    for key, value in defaults.items():
        node.setdefault(key, copy.deepcopy(value))
    node.setdefault("yrs", max(float(node["build_yrs"]), float(node["adopt_yrs"])))
    return node


def _remove(items: Dict[str, Any], claims: Dict[Any, str], kind: str, item_id: str,
            manifest: ModManifest, by_id: Dict[str, ModManifest], path: str) -> None:
    """Delete a base item on a mod's explicit request."""
    if item_id not in items:
        raise ModError("mod %s: %s removes missing %s %r" % (manifest.id, path, kind, item_id))
    claim_removal(claims, kind, item_id, manifest, by_id)
    del items[item_id]


def load_mod_tree(base_tree: Dict[str, Any], manifests: Iterable[ModManifest]) -> Dict[str, Any]:
    """Overlay mod branch nodes and goal catalog entries on a base tree."""
    tree = copy.deepcopy(base_tree)
    nodes = {node["id"]: node for node in tree["nodes"]}
    manifests = list(manifests)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    origins = {node_id: "data/tech_tree.json" for node_id in nodes}
    goals = list(tree.get("meta", {}).get("goals") or [])
    for manifest in manifests:
        for path in _json_files(os.path.join(manifest.directory, "data", "branches")):
            with open(path, encoding="utf-8") as source:
                payload = json.load(source)
            batch = payload.get("nodes", []) if isinstance(payload, dict) else payload
            for node in batch:
                if not isinstance(node, dict):
                    raise ModError("mod %s: %s contains a node that is not an object" %
                                   (manifest.id, path))
                node_id = node.get("replaces", node.get("id"))
                if not node_id:
                    raise ModError("%s contains a node without an id" % path)
                if node.get("remove") is True:
                    _remove(nodes, claims, TECH, node_id, manifest, by_id, path)
                    continue
                override = node.get("override") is True or "replaces" in node
                _check_new_id(manifest, node_id, override, path)
                if override:
                    check_not_removed(claims, TECH, node_id, manifest, by_id)
                if override and node_id not in nodes:
                    raise ModError("%s overrides missing tech node %r" % (path, node_id))
                if not override and node_id in nodes:
                    raise ModError("tech id %s is defined in both %s and %s" %
                                   (node_id, origins[node_id], path))
                if override:
                    # A patch names only the fields it changes; defaults are for new nodes.
                    claim_fields(claims, TECH, node_id, node, manifest, by_id)
                    nodes[node_id] = _deep_merge(nodes[node_id], dict(node, id=node_id))
                else:
                    if not isinstance(node.get("name"), str):
                        raise ModError("mod %s: node %s in %s is missing a string 'name'" %
                                       (manifest.id, node_id, path))
                    nodes[node_id] = _deep_merge({}, _node_defaults(dict(node)))
                origins[node_id] = path
        goals_path = os.path.join(manifest.directory, "data", "goals.json")
        if os.path.isfile(goals_path):
            with open(goals_path, encoding="utf-8") as source:
                for goal in json.load(source).get("goals", []):
                    if goal.get("remove") is True:
                        matching = [item for item in goals if item.get("node") == goal.get("node")]
                        if not matching:
                            raise ModError("%s removes missing goal for node %r" %
                                           (goals_path, goal.get("node")))
                        claim_removal(claims, GOAL, goal["node"], manifest, by_id)
                        goals = [item for item in goals if item not in matching]
                        continue
                    if goal.get("node") not in nodes:
                        raise ModError("%s names missing goal node %r" % (goals_path, goal.get("node")))
                    goals.append(goal)
    check_tree_references(nodes, goals, tree.get("meta", {}).get("goal_node"),
                          removed_by(claims, TECH))
    tree["nodes"] = list(nodes.values())
    tree.setdefault("meta", {})["goals"] = goals
    return tree


def load_mod_production(base: Dict[str, Any], manifests: Iterable[ModManifest]) -> Dict[str, Any]:
    merged = copy.deepcopy(base)
    manifests = list(manifests)
    by_id = {manifest.id: manifest for manifest in manifests}
    claims: Dict[Any, str] = {}
    for manifest in manifests:
        for path in _json_files(os.path.join(manifest.directory, "data", "production")):
            with open(path, encoding="utf-8") as source:
                entries = (json.load(source).get("materials") or {})
            for entry_id, entry in entries.items():
                if entry.get("remove") is True:
                    _remove(merged, claims, RECIPE, entry_id, manifest, by_id, path)
                    continue
                override = entry.get("override") is True
                _check_new_id(manifest, entry_id, override, path)
                if override:
                    check_not_removed(claims, RECIPE, entry_id, manifest, by_id)
                if override and entry_id not in merged:
                    raise ModError("%s overrides missing production recipe %r" % (path, entry_id))
                if not override and entry_id in merged:
                    raise ModError("production id %s is already defined before %s" % (entry_id, path))
                if override:
                    claim_fields(claims, RECIPE, entry_id, entry, manifest, by_id)
                merged[entry_id] = _deep_merge(merged.get(entry_id, {}), entry)
    check_recipe_references(merged, removed_by(claims, RECIPE))
    return merged
