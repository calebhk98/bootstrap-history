"""Does a civilisation's starting state agree with itself? (Complaints/128)

Pure data check, no engine and no civilisation ids. For each civilisation
file it reports three classes of contradiction between `starting_techs`, the
tree's own prerequisite graph, node costs and the production recipes:

  free_unheld      a node costing nothing (no capital, hours, labour,
                   materials or years) that the civilisation does not hold,
                   whose prerequisites it does hold or which are themselves
                   such nodes, and which no `needs_first` gate refuses. It
                   can be started at arrival for free: either the
                   civilisation should hold it, or the node should cost
                   something, or the civilisation should gate it.
  missing_prereq   a held node one of whose `pre` entries is not held
                   (Complaints/42 pins the known set by name; this only
                   reports it).
  unmakeable       a material a held node consumes whose every production
                   recipe is gated on a node the civilisation does not hold.

  rung_gap         a held node needs, directly or through other capability
                   nodes, a capability rung the civilisation does not hold
                   (a high heat rung held without the lower one).
  briefing         a held node the civilisation file's own `briefing_absent`
                   claims ({"claim": text, "nodes": [ids]}) say it lacks.

Used by `simulator.py validate`, and importable for tests.
"""
import glob
import json
import os

COST_FIELDS = ("cap_hours", "ph", "yrs", "build_yrs", "dev_years")


def is_free(node):
    """True when the node's own bill is entirely zero."""
    if any(node.get(field) for field in COST_FIELDS):
        return False
    return not (node.get("lab") or node.get("mat"))


def load_civilisations(root):
    civilisations = {}
    for path in sorted(glob.glob(os.path.join(root, "data", "civilizations", "*.json"))):
        name = os.path.basename(path)[:-len(".json")]
        if name.startswith("_"):
            continue
        with open(path, encoding="utf-8") as handle:
            civilisations[name] = json.load(handle)
    return civilisations


def gated_ids(civilisation, held):
    """Node ids a `needs_first` gate still refuses, given what is held."""
    gated = set()
    for key, entry in (civilisation.get("needs_first") or {}).items():
        if key.startswith("_") or not isinstance(entry, dict):
            continue
        if entry.get("node") and entry["node"] not in held:
            gated.update(entry.get("ids") or ())
    return gated


def free_unheld(nodes, civilisation):
    """Free nodes startable at arrival that the civilisation does not hold."""
    held = set(civilisation.get("starting_techs") or ())
    gated = gated_ids(civilisation, held)
    free_ids = {node_id for node_id, node in nodes.items()
                if is_free(node) and not node.get("win_condition")}
    reachable = set()
    changed = True
    while changed:
        changed = False
        for node_id in free_ids - held - reachable - gated:
            node = nodes[node_id]
            if not all(pre in held or pre in reachable for pre in node.get("pre") or ()):
                continue
            groups = node.get("req_any") or ()
            if any(not any(option in held or option in reachable
                           or option in (node.get("mat") or {})
                           or option not in nodes
                           for option in (group.get("options") or {}))
                   for group in groups):
                continue
            reachable.add(node_id)
            changed = True
    return sorted(reachable)


def missing_prerequisites(nodes, civilisation):
    """{held node: [prerequisites not held]}."""
    held = set(civilisation.get("starting_techs") or ())
    found = {}
    for node_id in sorted(held):
        node = nodes.get(node_id)
        if node is None:
            continue
        missing = sorted(pre for pre in node.get("pre") or () if pre not in held)
        if missing:
            found[node_id] = missing
    return found


def capability_rung_gaps(nodes, civilisation):
    """{held node: [capability nodes it implies that are not held]}.

    Walks prerequisites only through capability nodes, so a held rung needs
    every rung beneath it and a held tool needs the rungs it names."""
    held = set(civilisation.get("starting_techs") or ())

    def is_capability(node_id):
        return node_id in nodes and nodes[node_id].get("cat") == "capability"

    found = {}
    for node_id in sorted(held):
        if node_id not in nodes:
            continue
        seen = set()
        stack = [pre for pre in nodes[node_id].get("pre") or () if is_capability(pre)]
        while stack:
            rung = stack.pop()
            if rung in seen:
                continue
            seen.add(rung)
            stack.extend(pre for pre in nodes[rung].get("pre") or () if is_capability(pre))
        missing = sorted(seen - held)
        if missing:
            found[node_id] = missing
    return found


def briefing_contradictions(nodes, civilisation):
    """{claim: [held nodes the claim says are absent]}."""
    held = set(civilisation.get("starting_techs") or ())
    found = {}
    for entry in civilisation.get("briefing_absent") or ():
        contradicted = sorted(node_id for node_id in entry.get("nodes") or () if node_id in held)
        if contradicted:
            found[entry.get("claim", "")] = contradicted
    return found


def _producers(production):
    """{material: [(gate node id or None, recipe)]}."""
    by_material = {}
    for key, entry in production.items():
        outputs = set(entry.get("outputs") or ()) | {key}
        gate = entry.get("requires_node", None)
        for material in outputs:
            by_material.setdefault(material, []).append((gate, entry))
    return by_material


def unmakeable_materials(nodes, civilisation, production):
    """{held node: [materials it consumes that no available recipe makes]}.

    A material with no recipe at all, or with one whose gate is absent or
    null, is not judged: only materials whose every recipe needs a node the
    civilisation does not hold are reported."""
    held = set(civilisation.get("starting_techs") or ())
    by_material = _producers(production)
    found = {}
    for node_id in sorted(held):
        node = nodes.get(node_id)
        if node is None:
            continue
        blocked = []
        for material in sorted(node.get("mat") or ()):
            recipes = by_material.get(material)
            if not recipes:
                continue
            gates = [gate for gate, _entry in recipes]
            if all(gate is not None and gate not in held for gate in gates):
                blocked.append(material)
        if blocked:
            found[node_id] = blocked
    return found


def check_all(nodes, civilisations, production):
    """{civilisation: {"free_unheld": [...], "missing_prereq": {...}, "unmakeable": {...}}}"""
    return {name: {"free_unheld": free_unheld(nodes, civilisation),
                   "missing_prereq": missing_prerequisites(nodes, civilisation),
                   "unmakeable": unmakeable_materials(nodes, civilisation, production),
                   "rung_gap": capability_rung_gaps(nodes, civilisation),
                   "briefing": briefing_contradictions(nodes, civilisation)}
            for name, civilisation in civilisations.items()}


def report_lines(results):
    """Per-civilisation summary lines for `validate`."""
    lines = []
    for name, found in sorted(results.items()):
        lines.append("  %-20s free-but-unheld %3d   held-without-prereq %3d   "
                     "unmakeable-material %3d   rung-gap %3d   briefing-contradiction %3d"
                     % (name, len(found["free_unheld"]), len(found["missing_prereq"]),
                        len(found["unmakeable"]), len(found["rung_gap"]),
                        len(found["briefing"])))
    return lines
