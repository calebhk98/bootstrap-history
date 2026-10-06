"""Merge the branch files in data/branches/ into one technology tree, in memory.

`build_tree` is what sim/engine/tree_source.py builds the base tree from.
`merge_problems` lists what `python3 sim/simulator.py validate` reports as
errors: an id defined twice, and every merge event that drops something a
branch author wrote.
"""
import collections
import json
import os
import re

from sim.engine.catalog import load_production_catalog, load_trade_registry, material_namespace
from sim.engine.node_defaults import NUMERIC_FIELDS, OPTIONAL_DEFAULTS
from sim.engine.tree_source import (META_FILE, MERGED_DUPLICATE_IDS_FILE, NO_MODS_DIRECTORY,
                                    ROOT)

DATA = os.path.join(ROOT, "data")
BR = os.path.join(DATA, "branches")


def load_trades():
    """Read trade identity from the base trade registry, without mods."""
    return set(load_trade_registry(ROOT, mods_dir=NO_MODS_DIRECTORY))


# Schema v2. `yrs`, `sus` and `gov` are v1 and are backfilled, not demanded.
# Only these are genuinely required. Everything else has a sane default, because
# rejecting a whole node over a missing `up` throws away real work.
# Availability is described by prerequisites, capabilities, and costs rather
# than a universal numeric rank.
REQUIRED = ["id","name","cat","pre","note"]


def _num(value, default=0.0):
    """Branch authors sometimes write a number as a string, or as a range like
    '200-400'. Coerce rather than crash, and fall back to the default."""
    if isinstance(value, (int, float)): return float(value)
    if isinstance(value, str):
        match = re.findall(r"-?\d+(?:\.\d+)?", value)
        if match: return float(match[0])
    return float(default)


def normalise_v2(node):
    for field, value in OPTIONAL_DEFAULTS.items():
        node.setdefault(field, json.loads(json.dumps(value)))
    for field in NUMERIC_FIELDS:
        node[field] = _num(node.get(field), OPTIONAL_DEFAULTS[field])
    node["risk"] = min(0.95, max(0.0, node["risk"]))
    for fld in ("lab","mat"):
        if not isinstance(node.get(fld), dict): node[fld] = {}
        else: node[fld] = {code: _num(value, 0) for code, value in node[fld].items()}
    if not isinstance(node.get("pre"), list): node["pre"] = []
    if not isinstance(node.get("traits"), list): node["traits"] = []
    """Accept either schema and leave the node in v2 shape with v1 fields
    backfilled, so the simulator and the audit keep working during the change."""
    if "build_yrs" not in node and "yrs" in node:
        years = float(node.get("yrs", 0) or 0)
        if years >= 5:
            node["build_yrs"], node["adopt_yrs"] = min(3.0, years / 3.0), years
        else:
            node["build_yrs"], node["adopt_yrs"] = years, 0.0
    node.setdefault("build_yrs", 0.0); node.setdefault("adopt_yrs", 0.0)
    node["yrs"] = max(float(node["build_yrs"]), float(node["adopt_yrs"]))
    node.setdefault("req_any", []); node.setdefault("traits", [])
    node.setdefault("dev_years", None); node.setdefault("dev_people", None)
    # v1 scalars are derived from traits so old code paths still run
    node.setdefault("gov", 0); node.setdefault("sus", 0)
    return node


# ---------------------------------------------------------------- MERGE
def load_aliases():
    """No aliases: a stale source identifier is a merge event, never silently translated."""
    return {}, set()


def load_material_namespace(tree_nodes=()):
    """Material identity: everything the production catalogue declares plus what tree nodes require."""
    production = load_production_catalog(ROOT, mods_dir=NO_MODS_DIRECTORY)
    return material_namespace(production, tree_nodes)


def load_merged_duplicate_ids():
    """Read the dedup record from data/branches/, not from tech_tree.json.

    This mapping is SOURCE, not output: it records a decision a human made
    (these two branch ids name the same technology, keep this one) and the
    merge cannot rederive it from the branch files themselves - the branch
    files still contain both spellings. Before this function existed, the
    mapping lived only in tech_tree.json's meta, which is generated; a
    rebuild from branches alone would have had no way to know which ids were
    duplicates and would have resurrected all of them. See the header in
    that file for the full story.

    A missing file means no ids have been deduped yet, not an error. A branches/ directory built for a small fixture (a test,
    or a from-scratch tree with nothing to dedup) is a legitimate state, and
    refusing to merge just because nobody has ever recorded a duplicate
    would make this file mandatory boilerplate rather than a record of an
    actual decision.
    """
    path = os.path.join(BR, MERGED_DUPLICATE_IDS_FILE)
    if not os.path.exists(path):
        return {}
    return json.load(open(path))["merged_duplicate_ids"]


class BuiltTree:
    """What one merge of the branch files produced: the tree and everything the merge noticed."""

    def __init__(self):
        self.tree = {"meta": {}, "nodes": []}
        self.errs, self.warns, self.losses, self.collisions = [], [], [], []
        self.added = self.updated = 0
        self.dangling = collections.Counter()


def build_tree():
    """Merge every branch file into a tree, in memory. Prints and writes nothing.

    Branch files are the only source: nothing is seeded from an earlier tree.
    If two files define one id the merge stops early with `collisions` set.
    """
    goods, valid_trades, alias, dropset, meta, retired = _merge_load_inputs()
    built = BuiltTree()
    nodes = {}
    # which branch file has claimed an id in this run, so a second claim is a collision
    branch_origin = {}
    known_ids = _all_branch_node_ids()
    for filename in sorted(os.listdir(BR)):
        if not filename.endswith(".json") or filename in (MERGED_DUPLICATE_IDS_FILE, META_FILE):
            continue
        file_added, file_updated = _merge_process_branch_file(
            filename, nodes, alias, dropset, goods, valid_trades, retired, branch_origin,
            built.errs, built.warns, built.losses, built.collisions, known_ids)
        built.added += file_added
        built.updated += file_updated
    if built.collisions:
        return built
    built.dangling = _merge_resolve_prerequisites(nodes, retired, built.losses)
    _merge_break_cycles(nodes, built.losses)
    meta["merged_duplicate_ids"] = retired
    built.tree = {"meta": meta, "nodes": [nodes[node_id] for node_id in sorted(nodes)]}
    return built


def _merge_load_inputs():
    """The merge's read side: material namespace, trade registry, branch metadata and the dedup record."""
    valid_trades = load_trades()
    alias, dropset = load_aliases()
    goods = load_material_namespace()
    # Ids retired by deduplication. Branch files still contain both spellings of a
    # technology that two authors invented independently; the record lives in the branches.
    retired = load_merged_duplicate_ids()
    return goods, valid_trades, alias, dropset, load_branch_meta(), retired


def load_branch_meta():
    """Tree-level metadata (title, goals, goal node) from the branch directory."""
    path = os.path.join(BR, META_FILE)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def _all_branch_node_ids():
    """Every id defined in any branch file, so a repair in one file can see ids
    that a later file defines."""
    ids = set()
    for filename in sorted(os.listdir(BR)):
        if not filename.endswith(".json") or filename in (MERGED_DUPLICATE_IDS_FILE, META_FILE):
            continue
        try:
            batch = json.load(open(os.path.join(BR, filename)))
        except Exception:
            continue
        if isinstance(batch, list):
            ids.update(node["id"] for node in batch if isinstance(node, dict) and "id" in node)
    return ids


def _merge_fix_self_referencing_prereqs(batch, filename, nodes, warns, known_ids=frozenset()):
    # Branch authors routinely refer to their OWN nodes without the file's
    # id prefix: a file of ag2_* nodes asks for "coulter" when it means
    # "ag2_coulter". Left alone the prereq resolver below silently drops
    # those edges, which makes the technology look cheaper and earlier than
    # it is. Repair them here, but only where the fix is unambiguous.
    own = {node["id"] for node in batch if isinstance(node, dict) and "id" in node}
    prefixes = set()
    for node_id in own:
        if "_" in node_id:
            prefixes.add(node_id.split("_", 1)[0] + "_")
    for node in batch:
        if not isinstance(node, dict):
            continue
        fixed = []
        for prereq in node.get("pre", []):
            if prereq in own or prereq in nodes or prereq in known_ids:
                fixed.append(prereq)
                continue
            cands = {prefix + prereq for prefix in prefixes
                     if prefix + prereq in own and prefix + prereq != node.get("id")}
            if len(cands) == 1:
                resolved_prereq_id = cands.pop()
                fixed.append(resolved_prereq_id)
                warns.append("%s: %s self-ref '%s' -> '%s'" % (filename, node.get("id", "?"), prereq, resolved_prereq_id))
            else:
                fixed.append(prereq)
        if "pre" in node:
            node["pre"] = fixed


def _merge_resolve_labour(node, alias, valid_trades, filename, losses):
    # resolve trade aliases rather than silently dropping the labour,
    # which would make the technology look cheaper than it is
    lab = {}
    for trade, hours in node["lab"].items():
        resolved_trade = alias.get(trade, trade)
        if resolved_trade in valid_trades:
            lab[resolved_trade] = lab.get(resolved_trade, 0) + hours
        else:
            losses.append(("unknown_trade",
                "%s: %s unknown trade '%s', dropped" % (filename, node["id"], trade)))
    return lab


def _merge_resolve_materials(node, alias, dropset, goods, filename, losses):
    materials = {}
    for material, quantity in node["mat"].items():
        resolved_material = alias.get(material, material)
        if resolved_material not in goods:
            # generic fallbacks for the shapes authors actually write:
            # "mat_beeswax" -> "beeswax_kg", "plaster" -> "plaster_kg"
            for cand in (resolved_material[4:] + "_kg" if resolved_material.startswith("mat_") else None,
                         resolved_material + "_kg", resolved_material.replace("mat_", "")):
                if cand and cand in goods:
                    resolved_material = cand
                    break
        if resolved_material in dropset or material in dropset:
            losses.append(("material_is_technology",
                "%s: %s '%s' is a technology not a material, dropped" % (filename, node["id"], material)))
            continue
        if resolved_material in goods:
            materials[resolved_material] = materials.get(resolved_material, 0) + quantity
        else:
            losses.append(("undeclared_material",
                "%s: %s UNDECLARED material '%s', dropped" % (filename, node["id"], material)))
    return materials


def _merge_relocate_kb_prose(node):
    # Branch authors keep writing the RECIPE PROSE into the kb link
    # field. Left alone it reports as a broken link to a file whose
    # name is a sentence. Move it to note where note is empty and
    # clear the field, so it reports as an honest documentation gap.
    kb_field = str(node.get("kb", "")).strip()
    if kb_field and not re.match(r"^\d\d_[A-Za-z0-9_]+\.md(#|$)", kb_field):
        if not str(node.get("note", "")).strip():
            node["note"] = kb_field
        kb_field = ""
    node["kb"] = kb_field


def _merge_ingest_node(node, filename, nodes, alias, dropset, goods, valid_trades, retired, branch_origin, errs, warns, losses, collisions):
    """Validate, normalise and fold ONE branch node into `nodes`. Returns "added",
    "updated" or None (nothing ingested - a missing field, a retired id, or a
    same-run collision, each already recorded in errs/warns/collisions)."""
    override = node.get("override") is True or "replaces" in node
    if "replaces" in node:
        node.setdefault("id", node["replaces"])
    missing = [field for field in REQUIRED if field not in node]
    if missing:
        errs.append("%s: %s missing fields %s" % (filename, node.get("id", "?"), missing))
        return None
    if node["id"] in retired:
        warns.append("%s: %s was merged into %s, skipping"
                     % (filename, node["id"], retired[node["id"]]))
        return None
    if override and node["id"] not in nodes:
        errs.append("%s: %s claims an override but the target does not exist"
                    % (filename, node["id"]))
        return None
    if node["id"] in branch_origin and not override:
        # Two branch definitions claim the same id this run - either
        # the same file lists it twice, or two DIFFERENT files do.
        # Unlike the tree-vs-branch case below, there is no
        # source-of-truth rule that resolves this automatically: it is
        # either two authors who independently invented the same id,
        # or one author trying to "correct" a node by adding a second
        # definition in a new file instead of editing the original.
        # Guessing which is which is exactly the kind of silent
        # decision that ate branch edits in the first place, so this
        # is an ERROR naming both sides (sim/engine/validate_production.py's
        # load_production already applies the identical rule to
        # data/production/), not a warning, and the first definition
        # encountered is kept unchanged rather than overwritten.
        first = branch_origin[node["id"]]
        collisions.append(("%s is defined twice in %s" % (node["id"], filename))
                          if first == filename else
                          ("%s is defined in both %s and %s" % (node["id"], first, filename)))
        return None
    existed_in_tree = node["id"] in nodes
    # Tier 9 meant UNOBTAINABLE and that concept was abolished: nothing
    # is unobtainable, only elsewhere. A new branch reintroduced it on
    normalise_v2(node)
    node.pop("override", None)
    node.pop("replaces", None)
    node["lab"] = _merge_resolve_labour(node, alias, valid_trades, filename, losses)
    node["mat"] = _merge_resolve_materials(node, alias, dropset, goods, filename, losses)
    _merge_relocate_kb_prose(node)
    node["_src"] = filename
    # STAGE 3 (Complaints/30): a branch node that names an id already
    # present from the tree OVERWRITES it field by field, instead of
    # being silently dropped - the whole point of this fix. It is a
    # field-level overlay, not a wholesale replacement, because the
    # tree carries fields no branch schema has ever had a key for -
    # `kind`, `kb_level`, `_total_cost`, `_internal` - written by
    # `judge`/`repair`/`apply-caps`, which read and rewrite
    # tech_tree.json directly and were never meant to round-trip
    # through branches (see this file's module docstring and the
    # REPAIR PASS comment on cmd_repair). A replacement would silently
    # erase every one of those on every node a branch edit touches;
    # measured on the real tree, that is thousands of fields lost for
    # reasons that have nothing to do with what the branch author
    # wrote. `normalise_v2` only ever sets the keys in `DEFAULTS`
    # (plus the handful of v1/v2 scalars it backfills), so `node`
    # here never carries those repair-only keys unless a branch file
    # explicitly set them - meaning the tree's copy survives untouched
    # for every id whose branch definition doesn't mention it, exactly
    # like a normal git-free field merge.
    if existed_in_tree:
        nodes[node["id"]] = {**nodes[node["id"]], **node}
        status = "updated"
    else:
        nodes[node["id"]] = node
        status = "added"
    branch_origin[node["id"]] = filename
    return status


def _merge_process_branch_file(filename, nodes, alias, dropset, goods, valid_trades, retired, branch_origin, errs, warns, losses, collisions, known_ids=frozenset()):
    """Parse one branches/*.json file, fix its self-referencing prereqs, and ingest
    every node in it. Returns (added, updated) for this file alone."""
    try:
        batch = json.load(open(os.path.join(BR, filename)))
    except Exception as error:
        errs.append("%s: unparseable JSON: %s" % (filename, error))
        return 0, 0
    if not isinstance(batch, list):
        errs.append("%s: top level is not a list" % filename)
        return 0, 0

    _merge_fix_self_referencing_prereqs(batch, filename, nodes, warns, known_ids)

    added = updated = 0
    for node in batch:
        status = _merge_ingest_node(node, filename, nodes, alias, dropset, goods, valid_trades, retired, branch_origin, errs, warns, losses, collisions)
        if status == "added":
            added += 1
        elif status == "updated":
            updated += 1
    return added, updated


def _merge_resolve_prerequisites(nodes, retired, losses):
    # resolve prerequisites
    dangling = collections.Counter()
    for node in nodes.values():
        node["pre"] = [retired.get(prereq, prereq) for prereq in node["pre"]]
        for group in node.get("req_any", []):
            group["options"] = {retired.get(option, option): quantity for option, quantity in group.get("options", {}).items()}
        keep = []
        for prereq in node["pre"]:
            if prereq in nodes:
                keep.append(prereq)
            else:
                dangling[prereq] += 1
                losses.append(("unresolvable_prerequisite",
                    "%s: dropped unresolvable prereq '%s'" % (node["id"], prereq)))
        node["pre"] = keep
    return dangling


def _merge_break_cycles(nodes, losses):
    # break any cycles by dropping the back edge, reporting each one
    order, state = [], {}
    def dfs(i, stack):
        if state.get(i) == 2:
            return
        if state.get(i) == 1:
            back = stack[-1]
            nodes[back]["pre"] = [prereq for prereq in nodes[back]["pre"] if prereq != i]
            losses.append(("dependency_cycle", "CYCLE broken: removed %s -> %s" % (back, i)))
            return
        state[i] = 1
        for prereq in list(nodes[i]["pre"]):
            dfs(prereq, stack + [i])
        state[i] = 2
        order.append(i)
    for node_id in list(nodes):
        dfs(node_id, [])


def merge_problems(built):
    """What makes a merge unacceptable: an id defined twice, or an event that drops something a
    branch author wrote. `built.errs` (a node missing a required field) is reported, not refused."""
    return (["collision: " + collision for collision in built.collisions]
            + ["%s: %s" % (category, message) for category, message in built.losses])
