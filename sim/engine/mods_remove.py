"""Reference checks after mods remove content, and a scan of what was removed."""
import json
import os
from typing import Any, Dict, Iterable, Mapping

from .mods_base import ModError, ModManifest

TECH, RECIPE, TRADE, GOAL = "tech node", "production recipe", "trade", "goal"


def _read(path: str) -> Any:
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def _json_files(directory: str) -> Iterable[str]:
    if os.path.isdir(directory):
        for filename in sorted(os.listdir(directory)):
            if filename.endswith(".json"):
                yield os.path.join(directory, filename)


def scan_removed(manifests: Iterable[ModManifest], kind: str) -> Dict[str, str]:
    """Ids of this kind that mods mark `remove`, mapped to the removing mod."""
    found: Dict[str, str] = {}
    for manifest in manifests:
        data_dir = os.path.join(manifest.directory, "data")
        if kind == TECH:
            for path in _json_files(os.path.join(data_dir, "branches")):
                payload = _read(path)
                batch = payload.get("nodes", []) if isinstance(payload, dict) else payload
                found.update({node["id"]: manifest.id for node in batch
                              if isinstance(node, dict) and node.get("remove") is True})
        elif kind == RECIPE:
            for path in _json_files(os.path.join(data_dir, "production")):
                entries = _read(path).get("materials") or {}
                found.update({key: manifest.id for key, entry in entries.items()
                              if entry.get("remove") is True})
        elif kind == TRADE:
            path = os.path.join(data_dir, "world", "trades.json")
            if os.path.isfile(path):
                found.update({key: manifest.id for key, entry in
                              (_read(path).get("trades") or {}).items()
                              if isinstance(entry, dict) and entry.get("remove") is True})
    return found


def node_references(node: Mapping[str, Any]) -> Iterable[tuple]:
    """(role, referenced tech id) for every prerequisite a node names."""
    for target in node.get("pre") or ():
        yield "a prerequisite", target
    for group in node.get("req_any") or ():
        for target in (group.get("options") or {}):
            yield "a req_any option", target


def check_tree_references(nodes: Mapping[str, Any], goals: Iterable[Mapping[str, Any]],
                          goal_node: Any, removed: Mapping[str, str]) -> None:
    """Fail when remaining tech content still names a removed tech node."""
    def fail(owner: str, role: str, target: str) -> None:
        raise ModError("%s names removed tech node %s as %s; mod %s removed it" %
                       (owner, target, role, removed[target]))

    for node_id, node in nodes.items():
        for role, target in node_references(node):
            if target in removed and target not in nodes:
                fail("tech node %s" % node_id, role, target)
    for goal in goals:
        if goal.get("node") in removed and goal["node"] not in nodes:
            fail("goal for %s" % goal["node"], "its target", goal["node"])
    if goal_node in removed and goal_node not in nodes:
        fail("the tree's goal_node", "its target", goal_node)


def recipe_references(entry: Mapping[str, Any]) -> Iterable[str]:
    yield from (entry.get("inputs") or {})
    yield from (entry.get("outputs") or {})
    for capital in entry.get("capital") or ():
        yield from (capital.get("build_materials") or {})


def check_recipe_references(production: Mapping[str, Any], removed: Mapping[str, str]) -> None:
    """Fail when a remaining recipe uses a removed material nothing else produces."""
    produced = set(production)
    for entry in production.values():
        produced.update(entry.get("outputs") or {})
    for recipe_id, entry in production.items():
        for target in recipe_references(entry):
            if target in removed and target not in produced:
                raise ModError("production recipe %s uses %s, but mod %s removed the recipe "
                               "that produced it" % (recipe_id, target, removed[target]))


def check_trade_references(trades: Iterable[str], production: Mapping[str, Any],
                           nodes: Iterable[Mapping[str, Any]],
                           removed: Mapping[str, str]) -> None:
    """Fail when a recipe or technology still uses a removed trade."""
    def fail(owner: str, trade: str) -> None:
        raise ModError("%s uses removed trade %s; mod %s removed it" %
                       (owner, trade, removed[trade]))

    known = set(trades)
    for recipe_id, entry in production.items():
        used = list(entry.get("labour_hours") or {})
        for capital in entry.get("capital") or ():
            used.extend(capital.get("build_labour_hours") or {})
        for trade in used:
            if trade in removed and trade not in known:
                fail("production recipe %s" % recipe_id, trade)
    for node in nodes:
        for trade in node.get("lab") or {}:
            if trade in removed and trade not in known:
                fail("tech node %s" % node.get("id"), trade)
