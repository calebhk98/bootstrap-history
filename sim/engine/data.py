"""Loading the tree, the prices, the geography and the civilisations."""
#!/usr/bin/env python3
"""
ROME 100 AD -> TRANSISTOR : tech-tree simulator, planner and game.

  a RECORD : validate, costs, path   dump the tree and its economics
  a TOOL   : run, compare, sweep     Monte-Carlo a strategy, find where it breaks
  a GAME   : play, agent             step through it yourself, or let a script play

    python3 sim/simulator.py validate
    python3 sim/simulator.py civs                       who you can play
    python3 sim/simulator.py play --manual               free choice, no autopilot
    python3 sim/simulator.py agent --civ rome_100ad --fog

`agent` speaks one JSON object per line in and one per line out. It explains
itself: it prints a welcome on first run and answers {"cmd":"help"}. There is
no protocol document to read, on purpose.

No third-party dependencies. Python 3.8+.
Design notes and the full protocol: sim/PROTOCOL.md
"""

import argparse, json, math, os, random, sys
sys.setrecursionlimit(20000)
import collections
from collections import defaultdict, deque

# This file lives in sim/engine/, one level deeper than simulator.py used
# to, so the data directory is two parents up rather than one. Everything that
# reads a path reads it from here.
HERE = os.path.dirname(os.path.abspath(__file__))          # sim/engine
SIMDIR = os.path.dirname(HERE)                             # sim
ROOT = os.path.dirname(SIMDIR)                             # rome
TREE = os.path.join(ROOT, "data", "tech_tree.json")
PRICES = os.path.join(ROOT, "data", "prices.json")
STRATS = os.path.join(SIMDIR, "strategies")   # sim/strategies, beside simulator.py

# ----------------------------------------------------------------------------
# Loading and derived economics
# ----------------------------------------------------------------------------

CIVDIR = os.path.join(ROOT, "data", "civilizations")
RESFILE = os.path.join(ROOT, "data", "world", "resources.json")
GEOFILE = os.path.join(ROOT, "data", "world", "geography.json")

def load_resources():
    return json.load(open(RESFILE))

def load_geography():
    """Where things are, not just what they cost.

    geography.json used to carry a single hard-coded `reach` per region,
    measured from Italy, and nothing in this file ever read it: the `civs`
    command printed `base_reach` from the civ file and that was the entire
    effect either number had. Play Han China and the tree still behaved as
    though Italy were reach 0 and Malaya, which Chinese and Malay traders
    already sail to routinely, were an exotic reach-3 frontier. That is
    backwards for every civilization except Rome. See Sim.region_reach and
    Sim.material_reach for the fix: this loader just hands back the raw data.
    """
    return json.load(open(GEOFILE))


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance between two lat/lon points, in kilometres.

    Coarse on purpose: geography.json's coordinates are region centroids, not
    ports, so this is a reach ESTIMATE, the same spirit as everything else in
    this file being an order-of-magnitude model rather than a survey.
    """
    earth_radius_km = 6371.0
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    angular_term = (math.sin(dphi / 2) ** 2
                    + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlmb / 2) ** 2)
    return 2 * earth_radius_km * math.asin(math.sqrt(angular_term))

def _load_tech_effects():
    path = os.path.join(CIVDIR, "_TECH_EFFECTS.json")
    try:
        with open(path) as source:
            effects = json.load(source)
        return {key: value for key, value in effects.items() if not key.startswith("_")}
    except Exception:
        return {}


TECH_EFFECTS = _load_tech_effects()


def _load_wages():
    """The wage table, skipping the _note entry that is a bare string.

    My first version did `v["rate"]` over every entry, hit the explanatory
    _note string, raised, and a bare `except` turned that into an empty dict. So
    every trade reported "no such trade" and the error helpfully listed nothing
    at all. Swallowing an exception into a silent empty default is the same
    failure as the save file writing nulls: the bug is the except, not the data.
    """
    with open(PRICES) as source:
        prices_data = json.load(source)
    return {key: value["rate"] for key, value in prices_data["wage_rates_denarii_per_hour"].items()
            if isinstance(value, dict) and "rate" in value}


WAGES = _load_wages()


def _load_annual_wages():
    """What a year of one person of each trade actually costs.

    Two columns in prices.json disagree with each other by about half: `rate` is
    denarii an hour, `day_hs` is sestertii a day, and rate x 10 hours is
    consistently 1.5x day_hs / 4. The day figure is the better sourced of the
    two (it is what the wage evidence is actually quoted in), so annual pay
    comes from that where it exists, and only falls back to the hourly rate
    where it does not.
    """
    with open(PRICES) as source:
        prices_data = json.load(source)
    out = {}
    for trade, value in prices_data["wage_rates_denarii_per_hour"].items():
        if not isinstance(value, dict):
            continue
        if "day_hs" in value:
            out[trade] = value["day_hs"] / 4.0 * 250.0     # 4 sestertii to the denarius
        elif "rate" in value:
            out[trade] = value["rate"] * 2500.0
    return out


ANNUAL_WAGE = _load_annual_wages()


def _load_trade_notes():
    with open(PRICES) as source:
        prices_data = json.load(source)
    return {key: (value.get("note") or "") for key, value in prices_data["wage_rates_denarii_per_hour"].items()
            if isinstance(value, dict)}


TRADE_NOTES = _load_trade_notes()

# Trades that DO NOT EXIST in a pre-industrial society. The wage table already
# says so, in its own notes, for every one of them ("does not exist yet; you
# must create this trade"), so read it rather than keeping a second list that
# can drift out of step with the first.
TRADES_ABSENT = frozenset(trade for trade, note in TRADE_NOTES.items()
                          if "does not exist" in note.lower())

# What kind of person a trade is, for the two aggregate pools the tech tree asks
# for. A tester put the objection exactly: "a skilled blacksmith is not a skilled
# writer, but the game treats all as artisans". These are not interchangeable and
# from here on the model does not pretend they are.
TRADE_FAMILY = {
    "scholar": "scholar", "chemist": "scholar", "engineer": "scholar",
    "scribe": "scholar", "merchant": "scholar",
    "labourer": "labour", "miner": "labour", "sailor": "labour",
}   # everything else is a craft: smith, carpenter, mason, glassblower, ...


def trade_family(t):
    return TRADE_FAMILY.get(t, "craft")


# WHAT MONEY IS CALLED WHERE YOU ARE. Every civilisation file has carried a
# `currency` field since the schema was written and not one line of the engine
# ever read it, so an English player in 1300 counted denarii, hired against an
# equestrian census and was quoted for papyrus. The engine's arithmetic is all
# calibrated to Rome 100 AD through price_index, which is a real and defensible
# modelling choice; calling the unit a denarius in Tenochtitlan is not.
#
# The map is from the `currency` field to the form that reads correctly in a
# sentence like "you have 400 ___". A civilisation whose currency is not listed
# falls back to its own field, and then to denarii.
MONEY_WORDS = {
    "denarius": "denarii",
    "sterling penny": "pence",
    "wu zhu cash": "cash",
    "hacksilver by weight": "in hacksilver",
    "cacao bean and cotton cloth": "in cacao beans",
}


# THE SAME WORD IN BOTH FORMS, except for Rome where "den" is the established
# abbreviation and appears throughout the notes. Having a long form and a
# different short form produced sentences like "needs about 1959 pence, you
# have 612 den" - one clause localised from the payload, the next from the
# renderer - which a break tester quite reasonably filed as the currency
# drifting between three names.
MONEY_SHORT_WORDS = {
    "denarius": "den", "sterling penny": "pence", "wu zhu cash": "cash",
    "hacksilver by weight": "hacksilver", "cacao bean and cotton cloth": "beans",
}


def money_word(civ):
    cur = (civ or {}).get("currency") or "denarius"
    return MONEY_WORDS.get(cur, cur)


def money_short(civ):
    """The abbreviation used in compact lines: "400 den", "net +12 den/yr"."""
    cur = (civ or {}).get("currency") or "denarius"
    return MONEY_SHORT_WORDS.get(cur, MONEY_WORDS.get(cur, "den"))


def load_civ(name="rome_100ad"):
    """A civilization is DATA, not code. Swapping Rome for Han China, Viking
    Norway, Mexica Tenochtitlan or somewhere invented is a different file, not a
    different simulator. See data/civilizations/_SCHEMA.md."""
    path = os.path.join(CIVDIR, name + ".json")
    if not os.path.exists(path):
        # "_"-prefixed files are schema and reference data, not playable
        # civilizations - the same convention cli.py applies in both the places
        # it lists this directory, and the one place that did not, which is why
        # a play tester's typo was answered with "available: _TECH_EFFECTS,
        # england_1300, ...".
        have = sorted(filename[:-5] for filename in os.listdir(CIVDIR)
                      if filename.endswith(".json") and not filename.startswith("_"))
        raise SystemExit("unknown civilization %r. available: %s" % (name, ", ".join(have)))
    civ = json.load(open(path))
    # Opening ownership is scenario data, not an optional convenience with an
    # implicit fallback.  Silently turning a missing declaration into an empty
    # list makes a newly-authored scenario look valid while stripping its
    # entire inherited material/capability state.
    if "starting_techs" not in civ:
        raise ValueError("civilization %r must declare starting_techs explicitly"
                         % civ.get("id", name))
    if not isinstance(civ["starting_techs"], list):
        raise ValueError("civilization %r starting_techs must be a list"
                         % civ.get("id", name))
    duplicates = sorted(tech_id for tech_id, count in collections.Counter(
        civ["starting_techs"]).items() if count > 1)
    if duplicates:
        raise ValueError("civilization %r repeats starting technologies: %s"
                         % (civ.get("id", name), ", ".join(duplicates)))
    civ.setdefault("values", {})
    for field, default in (("w_military",0.5),("w_labour_saving",0.0),("w_information",0.0),
                 ("w_novelty",0.0),("w_magic_fear",0.4),("w_religious_rigidity",0.3),
                 ("w_commerce",0.3),("bribability",0.4),("patronage_weight",0.6),
                 ("adaptation_rate",0.10)):
        civ["values"].setdefault(field, default)
    return civ


def load(use_solved_prices=False, held_technology_ids=(), civilization_id=None):
    """Load the tree and `prices.json`, and derive each node's cost.

    `use_solved_prices` is OFF BY DEFAULT and every existing call site calls
    `load()` with no arguments, so this defaults to exactly the code path
    this function has always run: `goods` built straight from
    `prices.json`'s own `purchase_prices_denarii`, nothing imported, nothing
    solved. That is deliberate - see `sim/engine/prices.py`'s module
    docstring for the whole mechanism this is opting into and why it stays
    off until something asks for it - and it is why the import of
    `sim.engine.prices` below is INSIDE the `if`: a caller that never opts
    in never even imports the solver, let alone runs it.

    Passing `use_solved_prices=True` asks `sim.engine.prices` to solve a
    price for every material it can under `held_technology_ids` (an
    iterable of tech-tree node ids - typically a civilization's completed
    node set) and substitutes those into `goods` in place of the book
    figure, falling back to the book for anything the solver cannot yet
    price. The RETURN SHAPE is unchanged either way - still the same
    five-tuple every caller already unpacks - so this is a pure substitution
    of where `goods`'s numbers came from, not a new thing callers have to
    learn to read. Node costs (`_labour_cost`, `_material_cost`, `_total_cost`,
    `_hired_hours`) are then derived from `goods` exactly as before, so a
    solved material's price flows through to node cost the same way a book
    one always has.

    Use `goods_provenance()` below to see WHICH materials came from which
    source, independent of whether this switch is on - that report is the
    measurable burndown of `data/prices.json`, and it should be checkable
    without having to first flip the engine's own behaviour.

    `civilization_id` matters only when `use_solved_prices` is True: it
    decides whose held territory `iugerum_land` prices against (see
    `sim/engine/prices.py`'s RENT NEEDS A CIVILIZATION). It defaults to
    `None`, which `sim.engine.prices.priced_goods_table` resolves to Rome -
    the same default the standalone `sim/solve_prices.py --civ`-less run
    uses - so a caller pricing a NON-ROME civilization's goods table must
    pass its id here explicitly, or its land is silently priced as Rome's.
    """
    with open(TREE) as source:
        tree = json.load(source)
    with open(PRICES) as source:
        prices = json.load(source)
    nodes = {node["id"]: node for node in tree["nodes"]}
    wages = {key: value["rate"] for key, value in prices["wage_rates_denarii_per_hour"].items()
             if not key.startswith("_")}
    goods = {key: value["p"] for key, value in prices["purchase_prices_denarii"].items()
             if not key.startswith("_")}
    if use_solved_prices:
        from . import prices as price_solver
        goods, _provenance = price_solver.priced_goods_table(
            held_technology_ids, goods, prices,
            civilization_id=civilization_id)
    for node in nodes.values():
        node["_labour_cost"] = sum(wages[trade] * hours for trade, hours in node["lab"].items())
        node["_material_cost"] = sum(goods[material] * quantity for material, quantity in node["mat"].items())
        node["_total_cost"] = node["_labour_cost"] + node["_material_cost"] + node["cap"]
        node["_hired_hours"] = sum(node["lab"].values())
    return tree, prices, nodes, wages, goods


def goods_provenance(held_technology_ids=(), civilization_id=None):
    """{material: "solved" | "gated" | "no_recipe"} for every material
    `prices.json` prices, from `sim.engine.prices.priced_goods_table` - the
    burndown that measures "prices.json slowly deleted" one entry at a time
    (see that module's docstring). This always asks the solver, regardless
    of `load()`'s own `use_solved_prices` switch: the point is to be able to
    measure the split BEFORE deciding to turn the engine's own prices over
    to it, not only after.

    `civilization_id` should be the SAME civilization `held_technology_ids`
    came from - see `sim/engine/prices.py`'s RENT NEEDS A CIVILIZATION for
    why land rent needs to know this and cannot infer it from
    `held_technology_ids` alone. Left at `None` it prices land as Rome's,
    which is silently wrong for any other civilization's report.
    """
    with open(PRICES) as source:
        prices = json.load(source)
    goods = {key: value["p"] for key, value in prices["purchase_prices_denarii"].items()
             if not key.startswith("_")}
    from . import prices as price_solver
    _goods, provenance = price_solver.priced_goods_table(
        held_technology_ids, goods, prices, civilization_id=civilization_id)
    return provenance


# How many things rest on each node, for the whole tree at once.
#
# The old answer to "what depends on this" was, per node asked about:
#     blocks = {m for m in nodes if k in closure(nodes, m)}
# - a full ancestor closure of every one of 2,831 nodes, every time. That is
# affordable once, on `why`, and completely unaffordable for a table of thirty
# rows, which is why the number a normal-play tester said was the only one that
# decided anything was the one number `available` did not show. They ended up
# scripting 460 separate `why` calls to recover it, and wrote that "competent
# play degenerates into writing a scraper".
#
# So: one reverse-topological pass, descendants held as bitmasks in Python
# integers, computed once per tree and cached. Ordinary set unions would be
# 2,831 sets of up to 2,831 ids; an int OR is the same operation with the
# machine doing the work.
_DESC_CACHE = {}


def descendants(nodes):
    """{id: bitmask of everything downstream of it}, plus the index it uses."""
    # KEYED ON id(nodes) BUT VALIDATED BY IDENTITY, not by len(nodes).
    #
    # id() is only unique among objects that are alive at the same moment. A
    # freed dict's address goes to the next same-sized allocation, so a cache
    # that trusts a bare id() will hand a brand-new tree the index built for a
    # dead one. Validating on len(nodes) narrows that to "a different dict
    # that happens to have the same number of keys", which in a suite that
    # builds small synthetic node dicts by the hundred is not narrow at all.
    #
    # This exact hazard, in the sibling cache in economy.py, is what made the
    # simulation non-deterministic - see
    # Complaints/closed/27-nondeterministic-simulation.md. Holding `nodes` itself in
    # the entry keeps that dict alive for as long as the entry can be compared
    # against it, so its address cannot be recycled into a false hit while the
    # entry lives. sim/engine/proto/nodes.py makes the same argument at length
    # for the same shape of cache.
    hit = _DESC_CACHE.get(id(nodes))
    if hit is not None and hit[0] is nodes:
        return hit[1], hit[2]
    index = {node_id: i for i, node_id in enumerate(sorted(nodes))}
    kids = {node_id: [] for node_id in nodes}
    for m in nodes:
        for prereq_id in nodes[m]["pre"]:
            if prereq_id in kids:
                kids[prereq_id].append(m)
    # Iterative post-order DFS rather than topo_order(): that one rescans every
    # key for every key it pops, which is 8 million comparisons on this tree and
    # three and a half seconds of stall the first time anybody typed
    # "available". A DFS visits each edge once.
    masks = {}
    for root in sorted(nodes):
        if root in masks:
            continue
        stack = [(root, False)]
        while stack:
            node_id, expanded = stack.pop()
            if expanded:
                m = 0
                for child_id in kids[node_id]:
                    m |= (1 << index[child_id]) | masks.get(child_id, 0)
                masks[node_id] = m
                continue
            if node_id in masks:
                continue
            stack.append((node_id, True))
            for child_id in kids[node_id]:
                if child_id not in masks:
                    stack.append((child_id, False))
    _DESC_CACHE[id(nodes)] = (nodes, masks, index)
    return masks, index


def downstream_count(nodes, k):
    """How many nodes are downstream of k. Cheap after the first call."""
    masks, _index = descendants(nodes)
    return bin(masks.get(k, 0)).count("1")


def is_downstream(nodes, k, target):
    """Is `target` downstream of `k`?"""
    masks, index = descendants(nodes)
    if target not in index:
        return False
    return bool(masks.get(k, 0) >> index[target] & 1)


def hard_pre(nodes, k):
    """Every edge that is genuinely mandatory: `pre`, plus the `req_any` groups
    that offer exactly one real node and are therefore not a choice at all.

    ONE DEFINITION, used by closure(), topo_order() and critical_path()
    alike. They disagreed for a while: the closure learned to follow
    single-option groups and the other two did not, so `mat_manganese` was
    correctly listed as required and then topologically sorted AFTER the
    `mat_bulk_steel` that requires it, and the critical path was measured
    along a graph missing the edge. A requirement the ordering does not know
    about is a requirement the plan will schedule too late.

    Multi-option groups stay out. Those are real substitutions - silicon or
    germanium will do - and following all of them both overstates the work and
    cycles: junction_transistor -> silicon_path -> point_contact_transistor ->
    junction_transistor is a genuine loop once every option counts. `pre` plus
    the single-option edges alone is acyclic across all 2,833 nodes, checked
    directly, which is what makes this safe where the full walk is not.
    """
    # DEDUPED, in first-seen order. A node may name the same id in `pre` and
    # again in a single-option group - el2_valve_voltmeter_high_impedance
    # names vacuum_tube twice - and topo_order counts in-degree by walking
    # this list, so a duplicate raises the count by two against a decrement
    # that can only ever subtract one. The first version of this reported a
    # "cycle" among ten nodes that have no cycle between them at all: they
    # were simply the nodes Kahn's algorithm could never finish emitting.
    node = nodes[k]
    out, seen = [], set()
    for prereq_id in node["pre"]:
        if prereq_id not in seen:
            seen.add(prereq_id)
            out.append(prereq_id)
    for grp in (node.get("req_any") or []):
        opts = grp.get("options") or {}
        if len(opts) == 1:
            (opt,) = opts.keys()
            if opt in nodes and opt not in seen:
                seen.add(opt)
                out.append(opt)
    return out


def topo_order(nodes, subset=None):
    """Kahn topological sort. `subset` restricts to a set of ids.

    Was O(V^2 log V + V^2 E): every one of the (up to) 2,849 iterations of
    the main loop re-sorted every key in the tree and linear-scanned every
    node's prerequisite list looking for the id just emitted. 2.6s for the
    real tree, for what should be an O(V+E) pass.

    Rebuilds to the textbook version - a reverse-adjacency index built once
    (prereq -> the nodes that name it as a hard prerequisite), so emitting
    `k` only touches k's actual dependents - while reproducing the exact
    output order the old quadratic version produced, which the optimiser's
    `order` depends on byte-for-byte:
      (a) the initial ready list is sorted, same as before;
      (b) FIFO via collections.deque (O(1) popleft instead of list.pop(0)) -
          same emission order, just not O(n) per pop;
      (c) nodes newly at in-degree 0 are appended in sorted(keys) order
          WITHIN one outer iteration - reproduced here by sorting each
          node's own dependents list once, up front, so appending them in
          that fixed order during the walk matches what re-sorting all of
          `keys` and filtering would have produced each time.
    """
    keys = set(subset) if subset else set(nodes)
    hard_pre_by_node = {node_id: hard_pre(nodes, node_id) for node_id in keys}
    indeg = {node_id: 0 for node_id in keys}
    for node_id in keys:
        for prereq_id in hard_pre_by_node[node_id]:
            if prereq_id in keys:
                indeg[node_id] += 1
    # Reverse index: for each key, the OTHER keys that name it as a hard
    # prerequisite, in sorted order - the same relative order `sorted(keys)`
    # would have visited them in, since it is a subsequence of that sort.
    dependents = {node_id: [] for node_id in keys}
    for dependent_id in sorted(keys):
        for prereq_id in hard_pre_by_node[dependent_id]:
            if prereq_id in keys:
                dependents[prereq_id].append(dependent_id)
    ready = deque(sorted(node_id for node_id in keys if indeg[node_id] == 0))
    out = []
    while ready:
        node_id = ready.popleft()
        out.append(node_id)
        for dependent_id in dependents[node_id]:
            indeg[dependent_id] -= 1
            if indeg[dependent_id] == 0:
                ready.append(dependent_id)
    if len(out) != len(keys):
        raise RuntimeError("cycle detected among: %s" % sorted(keys - set(out)))
    return out


def closure(nodes, goal):
    """Everything the goal needs, following `pre` AND the `req_any` groups
    that are not really alternatives at all.

    A `req_any` group is a substitution: any one option satisfies it, so
    counting all of them as required would both overstate the work and cycle
    outright - `junction_transistor -> silicon_path -> point_contact_transistor
    -> junction_transistor` is a real loop once every option counts, and an
    earlier attempt to index the tree that way was OOM-killed by it.

    But 125 of the tree's groups have exactly ONE option naming a real node.
    That is not a choice between routes; it is a prerequisite that happened to
    be authored as a substitution group. `mat_bulk_steel`'s manganese_supply
    group is `{"mat_manganese": 1.0}` and nothing else, and because this walk
    used to follow `pre` alone, manganese was not in the goal's closure. A
    traced Rome run reached year 700 with 111 scholars, 428 artisans and 11.7
    million denarii and had still not built `mat_bulk_steel` or any of the 51
    nodes behind it - the whole road to the goal through steel, power and
    semiconductor purification - because the one tier-4 node in the way was
    never ranked ahead of the tree's 2,700 optional ones.

    Following the single-option groups takes the goal's closure from 158 nodes
    to 185 and cannot introduce a cycle: `pre` plus every single-option
    `req_any` edge in the whole 2,833-node tree is acyclic, checked directly.

    ONE RULEBOOK, deliberately. This lived as a separate `planning_closure` in
    planner.py for a few hours, on the reasoning that the shared walk had to
    stay as it was for fog and discovery. That reasoning is backwards: a
    mandatory prerequisite is mandatory for `validate`'s count, for `why`'s
    "full chain behind it" and for what the fog reveals, not only for the
    planner. A second copy of "what does the goal need" is how this project
    got a household capped at six scholars while its own optimizer held 146.
    """
    need, stack = set(), [goal]
    while stack:
        node_id = stack.pop()
        if node_id in need or node_id not in nodes:
            continue
        need.add(node_id)
        stack.extend(hard_pre(nodes, node_id))
    return need


def critical_path(nodes, goal):
    """Longest chain by minimum calendar years plus director-hours at one director.

    Iterative, over a topological order. The recursive version blew the stack once
    the tree passed a thousand nodes, which is a fair warning that this is no
    longer a toy graph.
    """
    need = closure(nodes, goal)
    order = topo_order(nodes, need)
    best = {}
    chain = {}
    for node_id in order:
        node = nodes[node_id]
        own = max(node["yrs"], node["ph"] / 2000.0)
        prereq_best, prereq_chain = 0.0, []
        for prereq_id in hard_pre(nodes, node_id):
            if prereq_id in best and best[prereq_id] > prereq_best:
                prereq_best, prereq_chain = best[prereq_id], chain[prereq_id]
        best[node_id] = prereq_best + own
        chain[node_id] = prereq_chain + [node_id]
    return best[goal], chain[goal]


# ----------------------------------------------------------------------------
# Goals: DATA, not code. One registry, `meta.goals` in tech_tree.json, that
# `validate`, `path`, `plan`, the menu's new-game wizard and every command
# below that takes `--goal` all read - so there is exactly one list of what
# a player or a measurement can aim at, not one opinion per command.
#
# A goal is always a real node id. An ordinary goal's node is the thing you
# build, the same as `junction_transistor` always was; a THRESHOLD-shaped
# goal (raise literacy past some level, cut epidemic mortality by some
# fraction) is a checkpoint node carrying a `win_condition` field instead of
# a normal cost - see projects.py's start_reason (which refuses to let
# anyone "start" one by hand) and core.py's per-year check (which completes
# it itself the moment the live measurement crosses the target). Either way
# `closure()`, `critical_path()`, `topo_order()` and `Sim.run()` take one
# node id and never need to know which kind it is; that is the whole point
# of modelling a threshold as a node rather than as a second mechanism.
# ----------------------------------------------------------------------------

def goal_catalog(tree, nodes=None):
    """The roster of selectable goals, in the order tech_tree.json lists
    them. Pass `nodes` to check every entry actually names a real node - a
    cheap check worth making once, in `validate`, rather than trusting the
    data file silently."""
    goals = tree["meta"].get("goals") or []
    if nodes is not None:
        bad = [goal_entry["node"] for goal_entry in goals if goal_entry.get("node") not in nodes]
        if bad:
            raise SystemExit("tech_tree.json meta.goals names nodes that do "
                             "not exist: %s" % ", ".join(bad))
    return goals


def goal_lookup(tree, node_id):
    """The goal_catalog entry for `node_id`, or None if it is not one of the
    named, selectable goals (an arbitrary node id is still a legal --goal
    for `path`/`plan` - see resolve_goal - it just has no menu entry)."""
    for goal_entry in tree["meta"].get("goals") or ():
        if goal_entry.get("node") == node_id:
            return goal_entry
    return None


def resolve_goal(tree, nodes, name):
    """The node id a `--goal` flag should resolve to: `name` itself if it
    names a real node, the tree's own default (meta.goal_node) if `name` is
    falsy, or a clear refusal naming the selectable goals otherwise. One
    function so every command that takes --goal agrees with every other one
    on what "no --goal" means and what an unknown one is told, instead of
    each command writing `a.goal or tree["meta"]["goal_node"]` itself and
    drifting - the same "one rulebook" reasoning as closure()'s own
    docstring, and this project has shipped that exact second-opinion bug
    enough times this week to stop inviting a sixth.
    """
    if not name:
        return tree["meta"]["goal_node"]
    if name not in nodes:
        known = ", ".join(sorted(goal_entry["node"] for goal_entry in tree["meta"].get("goals") or ()))
        raise SystemExit("no such goal or node: %r. Selectable goals: %s"
                         % (name, known))
    return name


# A node's `win_condition` names a metric Sim knows how to read (see
# core.py's _win_condition_value, the only other place this table is read),
# and this is the one place that turns it into a sentence a player can read
# - used when `start_reason` refuses to let anyone start one by hand, and
# anywhere else that explains what a threshold goal actually is. Each
# template takes the target value already formatted as a percentage; every
# metric here is a 0..1 fraction, which is the only shape `win_condition`
# currently supports and the only one either of the two current threshold
# goals needs.
WIN_CONDITION_LABELS = {
    "literacy_general": "the general population's literacy reaches %s",
    "literacy_elite": "the lettered and propertied class's literacy reaches %s",
    "epidemic_relief": ("the measures you have built have cut %s of what "
                        "epidemics and famine would otherwise take"),
}


def win_condition_describe(n):
    """The player-facing sentence for a node's win_condition, or a plain
    fallback for a metric this table does not yet name - never a KeyError,
    the same reasoning validate's own required-field check gives for why a
    missing piece of display data must degrade, not crash, a player's
    session."""
    win_condition = n.get("win_condition") or {}
    metric, comparison_op, val = win_condition.get("metric"), win_condition.get("op"), win_condition.get("value")
    pct = "%d%%" % round((val or 0.0) * 100)
    tmpl = WIN_CONDITION_LABELS.get(metric)
    if tmpl:
        return tmpl % pct
    return "a measurement (%s %s %s) is met" % (metric, comparison_op, val)


# ----------------------------------------------------------------------------
# Simulation
# ----------------------------------------------------------------------------

STARTING_KITS = {
    "destitute":   {"den": 0,     "desc": "the clothes you stand in. You must earn your first meal."},
    "poor_scholar":{"den": 400,   "desc": "DEFAULT. A few months' subsistence, a knife, a lens, a codex of notes. About what a working teacher has."},
    "artisan":     {"den": 1200,  "desc": "enough to rent a workshop and buy a first set of tools."},
    "merchant":    {"den": 4000,  "desc": "a modest trading capital. You can fund one real venture."},
    "rich_merchant":{"den": 20000,"desc": "wealthy but well under the equestrian census of 100,000."},
    "equestrian":  {"den": 100000,"desc": "the equestrian census exactly. Conspicuous."},
    # "the medians sit inside the noise band" is what this used to claim, and a
    # break tester called it false. They were right, though their measurement
    # (technologies built by year 12: 8 destitute, 51 poor_scholar, 143
    # rich_merchant) was of the OPENING rather than the finish, which is the
    # part money moves most. Measured on the finish as well - Rome, 8 runs a
    # kit, one seed - the median year the transistor is reached runs 476
    # destitute, 489 poor_scholar, 468 rich_merchant, 434 absurd. The first
    # three are inside each other's spread; a million denarii is not. So the
    # claim was true of the middle of the range and false at the top of it,
    # which is exactly the kind of statement that should not be made in one
    # sentence about "the whole kit range".
    "absurd":      {"den": 1000000,"desc": "four senatorial fortunes in unminted gold. It used to make things worse and no longer does: once money can be converted into protection and into sunk mines, wealth helps. What it does NOT do is make you a magician: a million denarii buys perhaps a tenth off the time, not a different game. What money changes most is the OPENING - the first fifty years, where a poor founder is choosing between eating and building."},
}

DEFAULTS = dict(
    # IMMORTALITY IS THE DEFAULT. The point of this simulator is to test the TREE,
    # and a mortality lottery that ends one run in five drowns the signal from the
    # technology in noise about how long one man happened to live. Turn death back
    # on with --mortal when you want to study succession instead of engineering.
    immortal=True,
    founder_life_mean=28.0,
    founder_life_sd=8.0,
    start_year=100,
    # DEFAULT IS A POOR SCHOLAR. Arriving with a noble's fortune is a strange
    # premise and the sweep shows it is also a worse one. Pick a kit with --kit.
    start_capital=400,
    founder_arrival_age=35,
    # 2,000, NOT 2,400. Everyone you HIRE is modelled at HOURS_PER_PERSON_YEAR
    # = 2,000 - "a 10-hour day, 250 days, less feasts" - and the founder was
    # given 2,400, twenty per cent more than a hired man, with no illness, no
    # travel, no administration and no bad weather. There is no story in which
    # the same person-year is worth more hours for you than for the smith you
    # pay. A modern 40-hour week over 52 weeks with no holiday at all is 2,080.
    founder_hours_per_year=2000,
    director_hours_per_year=1800,
    # WHAT "A PROVINCIAL TOWN'S LABOUR MARKET CAN SUPPLY" USED TO MEAN FOR
    # EVERY TRADE ALIKE - smith, scholar, millwright, all sharing one fixed
    # fraction of this single number. A player hired five blacksmiths and
    # watched the standing wage jump sharply, reasonably read that as a
    # claim about the Roman Empire's entire smithing capacity (nothing told
    # them otherwise) and called it absurd - correctly, for smiths. This is
    # still the baseline for the trades genuinely meant to be thin (scarce
    # or literacy-bound ones - see labour.py's market_supply): common, urban
    # trades now read a realistically-sized town's worth of their own
    # (labour.py's TOWN_POPULATION_REFERENCE and TRADE_DENSITY, cited
    # there) instead of a fraction of this number, which is why it did not
    # need to change.
    hired_hours_cap_base=25000,
    revenue_ramp_years=3,
    suspicion_danger=25.0,
    eminence_danger=26.0,
    horizon_years=500,
)
