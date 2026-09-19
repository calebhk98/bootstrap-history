#!/usr/bin/env python3
"""Tech-tree merge and PER-TECHNOLOGY audit.

The point of this file is the `judge` command.

The first version of this project graded itself on ONE number: what year the
simulation reached a transistor. That is the wrong test. A tree can produce a
plausible-looking end date while being wrong about almost every node in it.
The right test is whether each technology, taken ON ITS OWN, is honestly
specified: does it declare the capabilities it actually needs, is its cost
proportionate, could someone holding only its prerequisites really build it.

`judge` scores every node in isolation and reports the defects by name.

    python3 sim/treetool.py merge          # branches -> tech_tree.json
    python3 sim/treetool.py judge          # score every node, summary
    python3 sim/treetool.py judge --full   # every defect, node by node
    python3 sim/treetool.py judge --id X   # one node's report card
    python3 sim/treetool.py judge --grade D  # only nodes at or below D
"""
import argparse, json, os, re, sys, collections, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
# Guarded, idempotent - see sim/engine/commodities.py's own comment at the
# identical snippet for why a script that may be reached either directly
# (`python3 sim/treetool.py`, which only gets sim/ itself on sys.path for
# free) or through `from sim import treetool` (which gets the repository
# root but not necessarily sim/ itself) needs to put the repository root on
# sys.path explicitly rather than trust either caller to have done it.
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from sim.presentation import (                                   # noqa: E402
    MERGE_ERRORS_SHOWN, MERGE_WARNINGS_SHOWN,
    JUDGE_UNOBTAINABLE_DEPENDENCIES_SHOWN, JUDGE_NEAR_MATCH_SUGGESTIONS_SHOWN,
    JUDGE_WORST_NODES_SHOWN, JUDGE_NODE_ID_COLUMN_WIDTH_CHARS,
    JUDGE_DEFECT_CODES_SHOWN, APPLY_CAPS_SAMPLE_SHOWN,
    APPLY_CAPS_PREREQ_LIST_TRUNCATE_CHARS, APPLY_CAPS_REASON_TRUNCATE_CHARS)
DATA = os.path.join(ROOT, "data")
BR   = os.path.join(DATA, "branches")
TREE = os.path.join(DATA, "tech_tree.json")

def load_trades():
    """Read the trade list from prices.json rather than hardcoding it, so adding
    a trade to the price file is enough to make it usable."""
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    return set(trade for trade in prices["wage_rates_denarii_per_hour"] if not trade.startswith("_"))

# Schema v2. `yrs`, `sus` and `gov` are v1 and are backfilled, not demanded.
# Only these are genuinely required. Everything else has a sane default, because
# rejecting a whole node over a missing `up` throws away real work.
# Availability is described by prerequisites, capabilities, and costs rather
# than a universal numeric rank.
REQUIRED = ["id","name","cat","pre","note"]
DEFAULTS = {"ph":60,"lab":{},"mat":{},"cap":200,"up":40,"risk":0.15,"rev":0,
            "sch":0,"art":1,"conf":"C","kb":""}

def _num(v, d=0.0):
    """Branch authors sometimes write a number as a string, or as a range like
    '200-400'. Coerce rather than crash, and fall back to the default."""
    if isinstance(v, (int, float)): return float(v)
    if isinstance(v, str):
        match = re.findall(r"-?\d+(?:\.\d+)?", v)
        if match: return float(match[0])
    return float(d)


def normalise_v2(n):
    for field, value in DEFAULTS.items():
        n.setdefault(field, json.loads(json.dumps(value)))
    for field, default in (("ph",60),("cap",200),("up",40),("risk",0.15),("rev",0),
                 ("sch",0),("art",1)):
        n[field] = _num(n.get(field), default)
    n["risk"] = min(0.95, max(0.0, n["risk"]))
    for fld in ("lab","mat"):
        if not isinstance(n.get(fld), dict): n[fld] = {}
        else: n[fld] = {code: _num(value, 0) for code, value in n[fld].items()}
    if not isinstance(n.get("pre"), list): n["pre"] = []
    if not isinstance(n.get("traits"), list): n["traits"] = []
    """Accept either schema and leave the node in v2 shape with v1 fields
    backfilled, so the simulator and the audit keep working during the change."""
    if "build_yrs" not in n and "yrs" in n:
        years = float(n.get("yrs", 0) or 0)
        if years >= 5:
            n["build_yrs"], n["adopt_yrs"] = min(3.0, years / 3.0), years
        else:
            n["build_yrs"], n["adopt_yrs"] = years, 0.0
    n.setdefault("build_yrs", 0.0); n.setdefault("adopt_yrs", 0.0)
    n["yrs"] = max(float(n["build_yrs"]), float(n["adopt_yrs"]))
    n.setdefault("req_any", []); n.setdefault("traits", [])
    n.setdefault("dev_years", None); n.setdefault("dev_people", None)
    # v1 scalars are derived from traits so old code paths still run
    n.setdefault("gov", 0); n.setdefault("sus", 0)
    return n

# ---------------------------------------------------------------- MERGE
def load_aliases():
    path = os.path.join(BR, "ALIASES.json")
    if not os.path.exists(path):
        return {}, set()
    aliases = json.load(open(path))
    return aliases.get("alias", {}), set(aliases.get("drop", []))


def load_prices():
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    return set(material for material in prices["purchase_prices_denarii"] if not material.startswith("_"))


MERGED_DUPLICATE_IDS_FILE = "_MERGED_DUPLICATE_IDS.json"


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

    A missing file means no ids have been deduped yet, not an error - the
    same "absent means empty" reading load_aliases() already gives a missing
    ALIASES.json. A branches/ directory built for a small fixture (a test,
    or a from-scratch tree with nothing to dedup) is a legitimate state, and
    refusing to merge just because nobody has ever recorded a duplicate
    would make this file mandatory boilerplate rather than a record of an
    actual decision.
    """
    path = os.path.join(BR, MERGED_DUPLICATE_IDS_FILE)
    if not os.path.exists(path):
        return {}
    return json.load(open(path))["merged_duplicate_ids"]


def cmd_merge(a):
    goods, TRADES, alias, dropset, base, retired, nodes = _merge_load_inputs()
    errs, warns, added, updated = [], [], 0, 0
    # STAGE 3 (Complaints/30): which branch file, if any, has already supplied
    # THIS RUN'S definition of an id. Seeding `nodes` from the current tree
    # above means every id starts present, so `node["id"] in nodes` cannot
    # tell a genuine edit (branch redefines an id the TREE carried over) apart
    # from a real collision (two branch files redefine the same id). This
    # dict is the difference: it only ever holds ids a BRANCH FILE, in THIS
    # run, has claimed, so a second claim by a different file is unambiguous.
    branch_origin = {}
    # Cross-branch-file collisions: sim/validate_production.py already treats
    # a key defined in two files of data/production/ as an ERROR naming both
    # sides rather than a silent "first one wins" (see its load_production).
    # Complaints/30 asks for the identical rule here. Collected separately
    # from `errs` so the merge can refuse to write while still reporting
    # everything else it found.
    collisions = []
    # Every event that DELETES something a branch author wrote: a labour
    # trade prices.json has no rate for, a material with no price, a
    # material that is really a technology, a prerequisite naming no node,
    # or a back edge cut to break a cycle. Collected separately from `warns`
    # (informational, does not lose data) so the merge can refuse to write
    # unless the operator explicitly accepts the loss. See the refusal block
    # below, after both loops that populate this list have run.
    losses = []

    for filename in sorted(os.listdir(BR)):
        if not filename.endswith(".json") or filename in ("ALIASES.json", MERGED_DUPLICATE_IDS_FILE):
            continue
        file_added, file_updated = _merge_process_branch_file(
            filename, nodes, alias, dropset, goods, TRADES, retired, branch_origin, errs, warns, losses, collisions)
        added += file_added
        updated += file_updated

    # A collision names an id whose correct content is genuinely undecided -
    # neither the "first file wins" nor the "last file wins" reading is a fix,
    # both are the same silent guess the branch-edit bug already made once.
    # Refuse to write 2.8 MB of data over an unresolved disagreement between
    # two branch files; report everything found first, then say why nothing
    # was written, matching how sim/validate_production.py surfaces the same
    # rule (it has nothing to write, so it can report and exit; this does).
    if _merge_report_collisions(errs, collisions):
        return 1

    dangling = _merge_resolve_prerequisites(nodes, retired, losses)

    _merge_break_cycles(nodes, losses)

    # `losses` now holds every event, from both loops above, that deleted
    # something a branch author wrote rather than merely warning about it:
    # an unknown labour trade, a material with no price, a material that is
    # really a technology, a prerequisite naming no node, or a back edge cut
    # to break a cycle. Print every one, grouped by kind - someone fixing
    # the source data needs to see every problem in one pass, not the first
    # 25 and a count of the rest. Refuse to write unless the operator passed
    # --accept-data-loss: the same "collect everything, report, do not
    # write" shape as the collision refusal above, because this merge
    # already deletes data silently today, and that is the bug Task 1 of
    # this pass exists to close.
    if _merge_report_losses(losses, getattr(a, "accept_data_loss", False)):
        return 1

    return _merge_write_and_summarize(base, nodes, retired, added, updated, errs, warns, dangling, a)


def _merge_load_inputs():
    """The merge's read side: prices, aliases, the current tree, the dedup record, and
    the seed `nodes` dict (current tree, normalised, with `_src` defaulted to "core")."""
    goods = load_prices()
    TRADES = load_trades()
    alias, dropset = load_aliases()
    base = json.load(open(TREE))
    # Ids retired by deduplication. Branch files still contain both spellings
    # of a technology that two authors invented independently, so without this
    # the next merge silently resurrects every duplicate. Read from source
    # (data/branches/_MERGED_DUPLICATE_IDS.json), not from tech_tree.json's
    # meta - that meta key is written BY this function, a few lines below the
    # end of this one, so treating it as an input would make the merge read
    # its own last output instead of the human decision it is supposed to
    # represent.
    retired = load_merged_duplicate_ids()
    nodes = {node["id"]: normalise_v2(node) for node in base["nodes"]}
    for node in nodes.values():
        node.setdefault("_src", "core")
    return goods, TRADES, alias, dropset, base, retired, nodes


def _merge_fix_self_referencing_prereqs(batch, filename, nodes, warns):
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
            if prereq in own or prereq in nodes:
                fixed.append(prereq)
                continue
            cands = {prefix + prereq for prefix in prefixes if prefix + prereq in own}
            if len(cands) == 1:
                resolved_prereq_id = cands.pop()
                fixed.append(resolved_prereq_id)
                warns.append("%s: %s self-ref '%s' -> '%s'" % (filename, node.get("id", "?"), prereq, resolved_prereq_id))
            else:
                fixed.append(prereq)
        if "pre" in node:
            node["pre"] = fixed


def _merge_resolve_labour(node, alias, TRADES, filename, losses):
    # resolve trade aliases rather than silently dropping the labour,
    # which would make the technology look cheaper than it is
    lab = {}
    for trade, hours in node["lab"].items():
        resolved_trade = alias.get(trade, trade)
        if resolved_trade in TRADES:
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
            losses.append(("unpriced_material",
                "%s: %s UNPRICED material '%s', dropped" % (filename, node["id"], material)))
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


def _merge_ingest_node(node, filename, nodes, alias, dropset, goods, TRADES, retired, branch_origin, errs, warns, losses, collisions):
    """Validate, normalise and fold ONE branch node into `nodes`. Returns "added",
    "updated" or None (nothing ingested - a missing field, a retired id, or a
    same-run collision, each already recorded in errs/warns/collisions)."""
    missing = [field for field in REQUIRED if field not in node]
    if missing:
        errs.append("%s: %s missing fields %s" % (filename, node.get("id", "?"), missing))
        return None
    if node["id"] in retired:
        warns.append("%s: %s was merged into %s, skipping"
                     % (filename, node["id"], retired[node["id"]]))
        return None
    if node["id"] in branch_origin:
        # Two branch definitions claim the same id this run - either
        # the same file lists it twice, or two DIFFERENT files do.
        # Unlike the tree-vs-branch case below, there is no
        # source-of-truth rule that resolves this automatically: it is
        # either two authors who independently invented the same id,
        # or one author trying to "correct" a node by adding a second
        # definition in a new file instead of editing the original.
        # Guessing which is which is exactly the kind of silent
        # decision that ate branch edits in the first place, so this
        # is an ERROR naming both sides (sim/validate_production.py's
        # load_production already applies the identical rule to
        # data/production/), not a warning, and the first definition
        # encountered is kept unchanged rather than overwritten.
        first = branch_origin[node["id"]]
        collisions.append(("%s is defined twice in %s" % (node["id"], filename))
                          if first == filename else
                          ("%s is defined in both %s and %s" % (node["id"], first, filename)))
        return None
    existed_in_tree = node["id"] in nodes and node["id"] not in branch_origin
    # Tier 9 meant UNOBTAINABLE and that concept was abolished: nothing
    # is unobtainable, only elsewhere. A new branch reintroduced it on
    normalise_v2(node)
    node["lab"] = _merge_resolve_labour(node, alias, TRADES, filename, losses)
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


def _merge_process_branch_file(filename, nodes, alias, dropset, goods, TRADES, retired, branch_origin, errs, warns, losses, collisions):
    """Parse one branches/*.json file, fix its self-referencing prereqs, and ingest
    every node in it. Returns (added, updated) for this file alone."""
    try:
        batch = json.load(open(os.path.join(BR, filename)))
    except Exception as e:
        errs.append("%s: unparseable JSON: %s" % (filename, e))
        return 0, 0
    if not isinstance(batch, list):
        errs.append("%s: top level is not a list" % filename)
        return 0, 0

    _merge_fix_self_referencing_prereqs(batch, filename, nodes, warns)

    added = updated = 0
    for node in batch:
        status = _merge_ingest_node(node, filename, nodes, alias, dropset, goods, TRADES, retired, branch_origin, errs, warns, losses, collisions)
        if status == "added":
            added += 1
        elif status == "updated":
            updated += 1
    return added, updated


def _merge_report_collisions(errs, collisions):
    """Print the collision report if any id was defined twice this run. Returns True
    (merge must refuse) when it printed one."""
    if not collisions:
        return False
    print("errors  : %d" % len(errs))
    for e in errs[:MERGE_ERRORS_SHOWN]:
        print("   " + e)
    print("\nMERGE REFUSED: %d id(s) defined in more than one branch file:" % len(collisions))
    for collision in collisions:
        print("   COLLISION " + collision)
    print("\nFix the branch files so each id has exactly one definition (rename one "
          "side, delete a stale duplicate, or fold them into a single node), then "
          "re-run merge. Nothing was written.")
    return True


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


def _merge_report_losses(losses, accept_data_loss):
    """Print every data-loss event, grouped by category. Returns True (merge must
    refuse) unless --accept-data-loss was passed."""
    if not losses:
        return False
    by_category = collections.defaultdict(list)
    for category, message in losses:
        by_category[category].append(message)
    print("\n%d event(s) would delete data during this merge:" % len(losses))
    for category in sorted(by_category):
        print("\n  %s (%d)" % (category, len(by_category[category])))
        for message in by_category[category]:
            print("     " + message)
    if not accept_data_loss:
        print("\nMERGE REFUSED: the %d event(s) listed above would each drop something a "
              "branch author wrote (an unpriced material, an unknown trade, a prerequisite "
              "naming no node, or a cycle-breaking edge deletion). Fix the source data - "
              "price the material, add the trade to prices.json, add the missing "
              "prerequisite node, or break the cycle by hand in the branch file - and "
              "re-run merge. If the loss is intended, re-run with --accept-data-loss to "
              "write anyway. Nothing was written." % len(losses))
        return True
    print("\n--accept-data-loss was passed: writing despite the %d event(s) above." % len(losses))
    return False


def _merge_write_and_summarize(base, nodes, retired, added, updated, errs, warns, dangling, a):
    base["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    base["meta"]["goal_node"] = "point_contact_transistor"
    base["meta"]["merged_duplicate_ids"] = retired
    _write_json(base, TREE, a)

    print("\nmerged  : %d nodes (%d added from branches, %d updated from branches)"
          % (len(nodes), added, updated))
    print("errors  : %d" % len(errs))
    for e in errs[:MERGE_ERRORS_SHOWN]:
        print("   " + e)
    print("warnings: %d" % len(warns))
    for warning in warns[:MERGE_WARNINGS_SHOWN]:
        print("   " + warning)
    if len(warns) > MERGE_WARNINGS_SHOWN:
        print("   ... %d more" % (len(warns) - MERGE_WARNINGS_SHOWN))
    if dangling:
        print("\nmost-wanted unresolved prereq ids (candidates for new nodes):")
        for prereq_id, value in dangling.most_common(20):
            print("   %-40s wanted by %d nodes" % (prereq_id, value))
    return 0


# ---------------------------------------------------------------- JUDGE
CAP_PREFIX = "cap_"

# Categories that are IDEAS, not artefacts. A theorem needs no furnace, and an
# earlier version of this audit cheerfully demanded a vacuum rung for Boolean
# algebra because the word "vacuum tube" appeared in its note. Keyword matching
# on prose is a blunt instrument and this is the guard rail.
ABSTRACT_CATS = {"mathematics","physics","theory","knowledge","social","institution",
                 "foundation","capability","unobtainable","information","method","logic",
                 "computing_theory","organization","organisation"}

# Deliberately narrow. A word that merely MENTIONS a capability is not evidence
# that the technology needs it; only words naming the physical operation count.
HEAT_WORDS = ("furnace","kiln","smelt","forge","calcin","roast","anneal","sinter",
              "crucible","blast furnace","retort","molten","tempering","quench")
TOL_WORDS  = ("tolerance","machined","bored","lathe","gauge block","ball bearing",
              "lead screw","piston","cylinder bore","micrometer","ground surface","lapped")
VAC_WORDS  = ("vacuum","evacuat","getter","cathode ray","discharge tube","incandescent",
              "torr","exhausted envelope")
PUR_WORDS  = ("zone refin","single crystal","ultrapure","semiconductor grade","dopant",
              "parts per billion","high purity","electrorefin")
ELEC_WORDS = ("dynamo","electric motor","electrolysis","electroplat","arc lamp",
              "generator","alternating current","transformer","electric furnace")


def closure(nodes, k):
    seen, stack = set(), [k]
    while stack:
        ancestor_id = stack.pop()
        if ancestor_id in seen:
            continue
        seen.add(ancestor_id)
        stack.extend(nodes[ancestor_id]["pre"])
    return seen


def _judge_abstract_defects(n):
    """The abstract-category half of judge_node: only NOTE-THIN and NO-CONF apply."""
    defects = []
    if len(n["note"]) < 60:
        defects.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
    if n["conf"] not in ("A", "B", "C"):
        defects.append(("NO-CONF", "confidence not stated"))
    return defects


def _judge_capability_defects(n, caps, ancestry, text):
    """CAP-NONE plus the per-word capability-rung checks (heat, tolerance, vacuum, purity, power)."""
    defects = []
    physical = bool(n.get("mat")) or n.get("cap", 0) >= 200
    if not caps and physical and len(ancestry) >= 3 and n["cat"] not in (
            "social", "institution", "mathematics", "physics", "foundation",
            "information", "capability"):
        defects.append(("CAP-NONE", "physical work with no capability rung in its chain "
                              "(furnace, tolerance, vacuum, purity, or power)"))

    def want(words, prefix, label):
        if any(word in text for word in words) and not any(cap_id.startswith(prefix) for cap_id in caps):
            defects.append(("CAP-" + label, "reads as needing a %s rung but none appears "
                                      "in its prerequisite chain" % label.lower()))
    want(HEAT_WORDS, "cap_heat_", "HEAT")
    want(TOL_WORDS, "cap_tol_", "TOL")
    want(VAC_WORDS, "cap_vac_", "VAC")
    want(PUR_WORDS, "cap_pure_", "PURITY")
    if any(word in text for word in ELEC_WORDS) and not any(cap_id.startswith("cap_power_") for cap_id in caps):
        defects.append(("CAP-POWER", "electrical work with no power rung in its chain"))
    return defects


def _judge_structural_defects(n, ancestry, unob):
    """SHALLOW (thin direct prerequisites under a deep ancestry) and BLOCKED (depends on
    something marked unobtainable)."""
    defects = []
    if len(n["pre"]) < 2 and 10 <= len(ancestry) < 25:
        defects.append(("SHALLOW", "%d direct prerequisite(s) and an ancestry only %d nodes deep"
                             % (len(n["pre"]), len(ancestry))))
    if unob and n["cat"] != "unobtainable":
        defects.append(("BLOCKED", "depends on %s, which is marked UNOBTAINABLE"
                             % ", ".join(sorted(unob)[:JUDGE_UNOBTAINABLE_DEPENDENCIES_SHOWN])))
    return defects


def _judge_cost_and_hours_defects(n, ancestry, stats):
    """COST-HIGH, HOURS-HIGH, HOURS-ZERO and NO-FLOOR."""
    defects = []
    category = n["cat"]
    med_cost = stats["cost"].get(category, 1)
    cost = n["_total_cost"]
    if med_cost > 0 and cost > med_cost * 25:
        defects.append(("COST-HIGH", "costs %s den, about %.0fx the median for category %s"
                               % (f"{cost:,.0f}", cost / med_cost, category)))
    if n["ph"] > 2000:
        defects.append(("HOURS-HIGH", "%s founder-hours, which is %.1f%% of a working life"
                                % (f"{n['ph']:,}", 100.0 * n["ph"] / 72000)))
    if len(ancestry) >= 3 and n["ph"] == 0 and n["cat"] not in ("capability", "material"):
        defects.append(("HOURS-ZERO", "non-foundational work costs the founder no hours"))
    if n.get("adopt_yrs", 0) >= 5 and n["yrs"] < 1:
        defects.append(("NO-FLOOR", "long adoption has a calendar floor under a year"))
    return defects


def _judge_documentation_and_social_defects(n, ancestry):
    """NOTE-THIN, NO-RECIPE, NO-CONF and SOCIAL-FLAT."""
    defects = []
    if len(n["note"]) < 60:
        defects.append(("NOTE-THIN", "note is %d characters" % len(n["note"])))
    if not n.get("kb") and n["cat"] not in ("capability", "material", "unobtainable"):
        defects.append(("NO-RECIPE", "no knowledge-base link"))
    if n["conf"] not in ("A", "B", "C"):
        defects.append(("NO-CONF", "confidence not stated"))
    if len(ancestry) >= 3 and not n.get("traits") and n["sus"] == 0 and n["gov"] == 0 \
            and n["cat"] not in ("capability", "material", "unobtainable", "mathematics", "physics"):
        defects.append(("SOCIAL-FLAT", "no traits and no scalar gov/sus"))
    return defects


def judge_node(n, nodes, stats):
    """Score one technology using its declared graph and category, not a rank."""
    if n["cat"] in ABSTRACT_CATS:
        defects = _judge_abstract_defects(n)
        return max(0, 100 - len(defects) * 12), defects

    ancestry = closure(nodes, n["id"])
    caps = {node_id for node_id in ancestry if node_id.startswith(CAP_PREFIX)}
    text = (n["name"] + " " + n["note"]).lower()
    unob = [node_id for node_id in ancestry if nodes[node_id]["cat"] == "unobtainable"]

    defects = []
    defects += _judge_capability_defects(n, caps, ancestry, text)
    defects += _judge_structural_defects(n, ancestry, unob)
    defects += _judge_cost_and_hours_defects(n, ancestry, stats)
    defects += _judge_documentation_and_social_defects(n, ancestry)

    weights = {"NO-RECIPE": 1, "CAP-NONE": 3, "CAP-HEAT": 2, "CAP-TOL": 2,
               "CAP-VAC": 2, "CAP-PURITY": 2, "CAP-POWER": 2, "SHALLOW": 3,
               "BLOCKED": 3, "COST-HIGH": 1, "HOURS-HIGH": 1, "HOURS-ZERO": 1,
               "NO-FLOOR": 1, "NOTE-THIN": 2, "NO-CONF": 1, "SOCIAL-FLAT": 1}
    penalty = sum(weights.get(code, 1) for code, _ in defects)
    return max(0, int(round(100 - penalty * 6))), defects

def grade(s):
    return "A" if s >= 90 else "B" if s >= 78 else "C" if s >= 64 else "D" if s >= 50 else "F"


def _judge_compute_costs(nodes, prices):
    """Set node["_total_cost"] for every node from labour hours, materials and cap, in place."""
    wages = {trade: value["rate"] for trade, value in prices["wage_rates_denarii_per_hour"].items() if not trade.startswith("_")}
    goods = {material: value["p"] for material, value in prices["purchase_prices_denarii"].items() if not material.startswith("_")}
    for node in nodes.values():
        node["_total_cost"] = (sum(wages.get(trade, 0) * hours for trade, hours in node["lab"].items())
                            + sum(goods.get(material, 0) * quantity for material, quantity in node["mat"].items()) + node["cap"])


def _judge_cost_stats(nodes):
    """Per-category median of node["_total_cost"], once _judge_compute_costs has set it.
    Shared by judge (via _judge_build_results) and repair, which both need the same
    median-cost baseline that COST-HIGH in judge_node compares against."""
    by_category_cost = collections.defaultdict(list)
    for node in nodes.values():
        by_category_cost[node["cat"]].append(node["_total_cost"])
    return {"cost": {cat: statistics.median(value)
                     for cat, value in by_category_cost.items()}}


def _judge_build_results(nodes, prices):
    """Cost every node, work out the per-category median cost, then judge every node."""
    _judge_compute_costs(nodes, prices)
    stats = _judge_cost_stats(nodes)

    results = {}
    for node_id, node in nodes.items():
        results[node_id] = judge_node(node, nodes, stats)
    return results


def _judge_print_single_node_report(a, nodes, results):
    """The `judge --id X` report card for one node."""
    if a.id not in nodes:
        near = [node_id for node_id in nodes if a.id.lower() in node_id.lower()]
        raise SystemExit("unknown node. near matches: %s" % (", ".join(near[:JUDGE_NEAR_MATCH_SUGGESTIONS_SHOWN]) or "none"))
    node, (score, node_defects) = nodes[a.id], results[a.id]
    print("%s  [%s]" % (node["name"], node["id"]))
    print("=" * 78)
    print("grade %s (%d/100)   %s   confidence %s"
          % (grade(score), score, node["cat"], node["conf"]))
    print("direct prerequisites : %d   full ancestry : %d nodes"
          % (len(node["pre"]), len(closure(nodes, a.id)) - 1))
    print("cost %s den   founder-hours %s   calendar floor %.1f yr   risk %.0f%%"
          % (f"{node['_total_cost']:,.0f}", f"{node['ph']:,}", node["yrs"], 100 * node["risk"]))
    caps = sorted(cap_id for cap_id in closure(nodes, a.id) if cap_id.startswith("cap_"))
    print("capability rungs in its chain: %s" % (", ".join(caps) if caps else "NONE"))
    print("\n%s\n" % node["note"])
    if node_defects:
        print("DEFECTS")
        for code, msg in node_defects:
            print("  [%s] %s" % (code, msg))
    else:
        print("No defects found by the automated checks.")


def _judge_print_summary(nodes, results):
    """The header block: node count, mean score, grade distribution, defects by frequency."""
    dist = collections.Counter(grade(score) for score, _ in results.values())
    defects = collections.Counter()
    for score, node_defects in results.values():
        for code, _ in node_defects:
            defects[code] += 1

    print("PER-TECHNOLOGY AUDIT: every node judged on its own, not on the end date")
    print("=" * 78)
    print("nodes judged : %d" % len(nodes))
    print("mean score   : %.1f/100" % statistics.mean(score for score, _ in results.values()))
    print("grades       : " + "  ".join("%s %d (%.0f%%)" % (grade_letter, dist[grade_letter], 100.0 * dist[grade_letter] / len(nodes))
                                        for grade_letter in "ABCDF"))
    print("\nDEFECTS BY FREQUENCY")
    for code, value in defects.most_common():
        print("   %-12s %4d  (%.0f%% of nodes)" % (code, value, 100.0 * value / len(nodes)))


def _judge_print_worst_nodes(results):
    print("\nWORST NODES")
    worst = sorted(results.items(), key=lambda entry: entry[1][0])[:JUDGE_WORST_NODES_SHOWN]
    for node_id, (score, node_defects) in worst:
        print("   %-34s %3d %s  %s" % (node_id[:JUDGE_NODE_ID_COLUMN_WIDTH_CHARS], score, grade(score), ", ".join(code for code, _ in node_defects[:JUDGE_DEFECT_CODES_SHOWN])))


def _judge_print_grade_filter(a, results):
    """`judge --grade X`: every node at or below that grade. No-op unless the flag was passed."""
    if not a.grade:
        return
    floor = "FDCBA".index(a.grade.upper())
    print("\nALL NODES AT GRADE %s OR WORSE" % a.grade.upper())
    for node_id, (score, node_defects) in sorted(results.items(), key=lambda entry: entry[1][0]):
        if "FDCBA".index(grade(score)) <= floor:
            print("   %-34s %3d %s  %s" % (node_id[:JUDGE_NODE_ID_COLUMN_WIDTH_CHARS], score, grade(score), ", ".join(code for code, _ in node_defects)))


def _judge_print_full_report(a, results):
    """`judge --full`: every defect, node by node. No-op unless the flag was passed."""
    if not a.full:
        return
    print("\nFULL REPORT")
    for node_id, (score, node_defects) in sorted(results.items(), key=lambda entry: entry[1][0]):
        if node_defects:
            print("\n%s  %d %s" % (node_id, score, grade(score)))
            for code, message in node_defects:
                print("    [%s] %s" % (code, message))


def _judge_write_judgement(results, a):
    _write_json({node_id: {"score": score, "grade": grade(score), "defects": [code for code, _ in node_defects]}
                 for node_id, (score, node_defects) in results.items()},
                os.path.join(DATA, "judgement.json"), a)
    if not getattr(a, "dry_run", False):
        print("\nwrote data/judgement.json")


def cmd_judge(a):
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    results = _judge_build_results(nodes, prices)

    if a.id:
        _judge_print_single_node_report(a, nodes, results)
        return 0

    _judge_print_summary(nodes, results)
    _judge_print_worst_nodes(results)
    _judge_print_grade_filter(a, results)
    _judge_print_full_report(a, results)
    _judge_write_judgement(results, a)
    return 0


# ---------------------------------------------------------------- REPAIR
PREFIX_MODULE = {
 "fud_":"75_agriculture_food.md","prn_":"80_information_printing.md",
 "lnd_":"85_transport_civil.md","sea_":"85_transport_civil.md","air_":"85_transport_civil.md",
 "pwr_":"40_power_precision.md","chm_":"20_chemistry.md","met_":"10_metallurgy.md",
 "prc_":"40_power_precision.md","med_":"70_medicine_biology.md","civ_":"85_transport_civil.md",
 "opt_":"30_glass_optics.md","tex_":"90_textiles.md","hom_":"91_household.md",
 # schema v2 branches
 "exp_":"95_expeditions.md","fin_":"96_finance.md","mil_":"97_military.md",
 "ch2_":"20_chemistry.md","el2_":"50_electricity.md","mfg_":"40_power_precision.md",
 "md2_":"70_medicine_biology.md","tr2_":"92_vehicles_flight.md","mt2_":"10_metallurgy.md",
 "tx2_":"90_textiles.md","ag2_":"75_agriculture_food.md","in2_":"30_glass_optics.md",
 "cv2_":"85_transport_civil.md","en2_":"93_energy.md","if2_":"80_information_printing.md",
 "sc2_":"60_mathematics_method.md",
}
# com_ splits: calculation and logic go to module 94, everything that moves a
# signal down a wire or through the air goes to module 50.
COMPUTING_WORDS = ("calc","comput","boolean","binary","logic","punch","hollerith",
                   "crypt","informatio","flip_flop","register","accumulator","memory",
                   "core","drum","tape","compiler","stored_program","error_","slide_rule",
                   "napier","difference_engine","analytical_engine","arithmometer",
                   "comptometer","ring_counter","integrated_circuit","photolith")
HEAT_BY_TIER = {0:"cap_heat_0700",1:"cap_heat_1100",2:"cap_heat_1300",3:"cap_heat_1300",
                4:"cap_heat_1600",5:"cap_heat_1600"}
TOL_BY_TIER  = {0:"cap_tol_1mm",1:"cap_tol_1mm",2:"cap_tol_100um",3:"cap_tol_10um",
                4:"cap_tol_10um",5:"cap_tol_1um"}
VAC_BY_TIER  = {3:"cap_vac_1torr",4:"cap_vac_1e3",5:"cap_vac_1e6"}
PUR_BY_TIER  = {3:"cap_pure_2N",4:"cap_pure_4N",5:"cap_pure_6N"}
PWR_BY_TIER  = {3:"cap_power_water",4:"cap_power_electric",5:"cap_power_grid"}

SOCIAL_DEFAULT = {
 # category substring -> (gov, sus) applied only where BOTH are still zero
 "military":(3,6), "weapon":(3,6), "explosive":(3,10), "chem":(0,6), "medicine":(2,4),
 "agricult":(3,0), "food":(2,0), "transport":(2,1), "rail":(3,1), "ship":(3,1),
 "aviation":(3,10), "flight":(3,10), "electr":(1,8), "power":(2,3), "metal":(2,2),
 "textile":(-1,1), "household":(0,1), "print":(-1,2), "media":(-1,3), "optic":(1,3),
 "instrument":(1,3), "civil":(2,0), "mining":(2,1), "precision":(1,1), "comput":(0,4),
 "communic":(3,3), "glass":(1,2),
}

def _repair_infer_capabilities(node, nodes, codes, counts):
    """Capability gaps remain visible for human review. A prose keyword
    heuristic cannot safely infer engineering prerequisites.

    `add()` below is the machinery for the heuristic that WOULD infer them -
    kept in this shape, not deleted, because an independent review found a
    100 percent error rate on the edges it produced (see --infer-caps' help
    text) and nothing in this function calls it. `added` therefore stays
    empty and the two blocks below it are always a no-op today; that is
    intentional, not a bug this pass introduced, and it is left wired exactly
    as found so a future author who turns --infer-caps back on sees what to
    call rather than having to reinvent it.
    """
    added = []
    def add(cap_id):
        # NEVER create a cycle. cap_heat_1100 depends on refractory_fireclay, so
        # giving refractory_fireclay a furnace rung (its note is full of furnace
        # words) makes the graph eat itself. An earlier version did exactly that.
        if not cap_id or cap_id in nodes and cap_id in node["pre"]:
            return
        if cap_id not in nodes:
            return
        if node["id"] in closure(nodes, cap_id):
            counts["cycle-forming edges refused"] += 1
            return
        node["pre"].append(cap_id); added.append(cap_id)
    if codes & {"CAP-NONE", "CAP-HEAT", "CAP-TOL", "CAP-VAC", "CAP-PURITY", "CAP-POWER"}:
        counts["capability gaps LEFT VISIBLE (not guessed at)"] += 1
    if added:
        counts["capability edges inferred"] += len(added)
        node["note"] = node["note"].rstrip() + (" [AUDIT: capability prerequisite(s) %s were "
            "inferred by sim/treetool.py repair, not stated by the author. Treat "
            "them as a floor, not a specification.]" % ", ".join(added))


def _repair_documentation_level(node, ident, counts):
    # documentation level
    if not node.get("kb"):
        if ident.startswith("com_"):
            doc_module = ("94_computing.md" if any(word in ident for word in COMPUTING_WORDS)
                   else "50_electricity.md")
        else:
            doc_module = next((value for pre, value in PREFIX_MODULE.items() if ident.startswith(pre)), None)
        if doc_module:
            node["kb"] = doc_module; node["kb_level"] = "module"; counts["module-level doc links"] += 1
        else:
            node["kb_level"] = "none"; counts["still undocumented"] += 1
    else:
        node["kb_level"] = "recipe" if "#" in node["kb"] else "module"


def _repair_social_defaults(node, ident, codes, counts):
    # social model
    if "SOCIAL-FLAT" in codes:
        haystack = (node["cat"] + " " + ident).lower()
        for category_marker, (gov_default, sus_default) in SOCIAL_DEFAULT.items():
            if category_marker in haystack:
                node["gov"], node["sus"] = gov_default, sus_default
                counts["social defaults applied"] += 1
                node["note"] = node["note"].rstrip() + (" [AUDIT: State interest and suspicion "
                    "were unset and have been defaulted from the category.]")
                break


def _repair_calendar_floor(node, codes, counts):
    if "NO-FLOOR" in codes:
        node["yrs"] = max(node["yrs"], 2.0); counts["calendar floors raised"] += 1


def cmd_repair(a):
    """Fix what the audit can fix mechanically, and MARK every inference.

    A tree whose capability prerequisites were inferred by a script is better
    than one where they are missing, but only if it says so. Every edge added
    here is recorded in the node so a reader can discount it.
    """
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    prices = json.load(open(os.path.join(DATA, "prices.json")))
    _judge_compute_costs(nodes, prices)
    stats = _judge_cost_stats(nodes)

    counts = collections.Counter()
    for ident, node in list(nodes.items()):
        if node["cat"] in ABSTRACT_CATS:
            continue
        score, defects = judge_node(node, nodes, stats)
        codes = {code for code, _ in defects}
        # Four independent repair rules: each reads only `codes` (already
        # computed above, before any of them run) and its own bit of `node`,
        # so the order between them changes nothing except, for the two that
        # both append to node["note"], the order the audit tags land in that
        # field - keep this exact call sequence to keep that order stable.
        _repair_infer_capabilities(node, nodes, codes, counts)
        _repair_documentation_level(node, ident, counts)
        _repair_social_defaults(node, ident, codes, counts)
        _repair_calendar_floor(node, codes, counts)
    tree["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("REPAIR PASS")
    for ident, value in counts.most_common():
        print("   %-32s %d" % (ident, value))
    return 0


def cmd_apply_caps(a):
    """Apply reviewer-assigned capability rungs from data/caps_fix_*.json.

    Unlike the keyword heuristic this replaces, every edge here was chosen by a
    reviewer looking at one node at a time with the failure modes of the previous
    attempt written into their brief. Each edge is still validated: it must name a
    real node, it must not already be present, and it must not create a cycle.
    """
    import glob
    tree = json.load(open(TREE))
    nodes = {node["id"]: node for node in tree["nodes"]}
    applied = refused = empty = unknown = 0
    reasons = {}
    for path in sorted(glob.glob(os.path.join(DATA, "review", "caps_fix_*.json"))):
        try:
            fixes = json.load(open(path))
        except Exception as e:
            print("unparseable: %s (%s)" % (os.path.basename(path), e))
            continue
        for node_id, fix in fixes.items():
            if node_id not in nodes:
                unknown += 1
                continue
            add = fix.get("add") or []
            if not add:
                empty += 1
                continue
            node = nodes[node_id]
            got = []
            for cap_id in add:
                if cap_id not in nodes:
                    refused += 1
                    continue
                if cap_id in node["pre"]:
                    continue
                if node_id in closure(nodes, cap_id):
                    refused += 1          # would make the graph eat itself
                    continue
                node["pre"].append(cap_id)
                got.append(cap_id)
                applied += 1
            if got:
                reasons[node_id] = (got, fix.get("reason", ""))
                node["note"] = node["note"].rstrip() + (
                    " [REVIEWED: prerequisite(s) %s added by a reviewer working node by node. "
                    "Reason: %s]" % (", ".join(got), fix.get("reason", "not given")))
    tree["nodes"] = [nodes[node_id] for node_id in sorted(nodes)]
    _write_json(tree, TREE, a)
    print("APPLY REVIEWER-ASSIGNED PREREQUISITES")
    print("   edges applied                    %d" % applied)
    print("   nodes judged to need none        %d" % empty)
    print("   edges refused (unknown or cycle) %d" % refused)
    print("   unknown node ids                 %d" % unknown)
    print("\nsample of what was added:")
    for node_id, (got, why) in list(reasons.items())[:APPLY_CAPS_SAMPLE_SHOWN]:
        print("   %-34s + %-38s %s" % (node_id[:JUDGE_NODE_ID_COLUMN_WIDTH_CHARS],
                                       ", ".join(got)[:APPLY_CAPS_PREREQ_LIST_TRUNCATE_CHARS],
                                       why[:APPLY_CAPS_REASON_TRUNCATE_CHARS]))
    return 0


# WRITING IS A CHOICE, AND IT WAS NOT BEING OFFERED. Every one of this tool's
# four subcommands rewrote a committed data file - tech_tree.json (2.8 MB) or
# judgement.json (244 KB) - unconditionally, at the end of its run, with no way
# to ask any of them merely to LOOK. So `judge`, which reads as a report
# command and prints a report, silently replaced 244 KB of committed game data
# as a side effect of being run; an agent doing nothing but timing it wiped the
# file and only noticed because git said so. A tool whose read-only-sounding
# verb mutates the repository is a trap, and it caught the first person to
# walk past it.
#
# --dry-run says what would be written and writes nothing. The default is
# unchanged - these commands still write, because that is what they are for
# and existing callers depend on it - so this only adds a way to be careful.
def _write_json(obj, path, a, indent=1):
    """json.dump, unless --dry-run was asked for."""
    if getattr(a, "dry_run", False):
        print("would write %s (--dry-run: not written)" % os.path.basename(path))
        return
    json.dump(obj, open(path, "w"), indent=indent)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="cmd", required=True)
    subparser = subparsers.add_parser("merge")
    subparser.add_argument("--accept-data-loss", action="store_true",
                   help="write the merge even though it will delete data: drop an unpriced "
                        "material, drop a labour trade prices.json has no rate for, drop a "
                        "material that is really a technology, drop a prerequisite that names "
                        "no node, or delete a back edge to break a dependency cycle. Without "
                        "this flag the merge lists every such event and refuses to write, so "
                        "the default is to fix the source branch files instead. Pass this only "
                        "once you have looked at the printed list and decided the loss is "
                        "correct.")
    subparsers.add_parser("apply-caps")
    subparser = subparsers.add_parser("repair")
    subparser.add_argument("--infer-caps", action="store_true",
                   help="guess missing capability rungs from keywords. OFF BY DEFAULT: an "
                        "independent review found a 100 percent error rate on the edges this "
                        "produced. Every edge it adds must be reviewed by hand.")
    subparser = subparsers.add_parser("judge")
    subparser.add_argument("--full", action="store_true")
    subparser.add_argument("--id")
    subparser.add_argument("--grade")
    # ON EVERY SUBCOMMAND, not only the ones that look dangerous: all four
    # write a committed data file, and which ones those are is exactly the
    # thing a person running this for the first time does not know.
    for command_parser in subparsers.choices.values():
        command_parser.add_argument("--dry-run", action="store_true",
                         help="say what would be written, write nothing")
    args = parser.parse_args()
    return {"merge": cmd_merge, "judge": cmd_judge, "repair": cmd_repair,
            "apply-caps": cmd_apply_caps}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main() or 0)
