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
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def _load_tech_effects():
    p = os.path.join(CIVDIR, "_TECH_EFFECTS.json")
    try:
        with open(p) as source:
            effects = json.load(source)
        return {k: v for k, v in effects.items() if not k.startswith("_")}
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
        p = json.load(source)
    return {k: v["rate"] for k, v in p["wage_rates_denarii_per_hour"].items()
            if isinstance(v, dict) and "rate" in v}


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
        p = json.load(source)
    out = {}
    for k, v in p["wage_rates_denarii_per_hour"].items():
        if not isinstance(v, dict):
            continue
        if "day_hs" in v:
            out[k] = v["day_hs"] / 4.0 * 250.0     # 4 sestertii to the denarius
        elif "rate" in v:
            out[k] = v["rate"] * 2500.0
    return out


ANNUAL_WAGE = _load_annual_wages()


def _load_trade_notes():
    with open(PRICES) as source:
        p = json.load(source)
    return {k: (v.get("note") or "") for k, v in p["wage_rates_denarii_per_hour"].items()
            if isinstance(v, dict)}


TRADE_NOTES = _load_trade_notes()

# Trades that DO NOT EXIST in a pre-industrial society. The wage table already
# says so, in its own notes, for every one of them ("does not exist yet; you
# must create this trade"), so read it rather than keeping a second list that
# can drift out of step with the first.
TRADES_ABSENT = frozenset(t for t, note in TRADE_NOTES.items()
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
    f = os.path.join(CIVDIR, name + ".json")
    if not os.path.exists(f):
        # "_"-prefixed files are schema and reference data, not playable
        # civilizations - the same convention cli.py applies in both the places
        # it lists this directory, and the one place that did not, which is why
        # a play tester's typo was answered with "available: _TECH_EFFECTS,
        # england_1300, ...".
        have = sorted(x[:-5] for x in os.listdir(CIVDIR)
                      if x.endswith(".json") and not x.startswith("_"))
        raise SystemExit("unknown civilization %r. available: %s" % (name, ", ".join(have)))
    c = json.load(open(f))
    # Opening ownership is scenario data, not an optional convenience with an
    # implicit fallback.  Silently turning a missing declaration into an empty
    # list makes a newly-authored scenario look valid while stripping its
    # entire inherited material/capability state.
    if "starting_techs" not in c:
        raise ValueError("civilization %r must declare starting_techs explicitly"
                         % c.get("id", name))
    if not isinstance(c["starting_techs"], list):
        raise ValueError("civilization %r starting_techs must be a list"
                         % c.get("id", name))
    duplicates = sorted(k for k, count in collections.Counter(
        c["starting_techs"]).items() if count > 1)
    if duplicates:
        raise ValueError("civilization %r repeats starting technologies: %s"
                         % (c.get("id", name), ", ".join(duplicates)))
    c.setdefault("values", {})
    for k, d in (("w_military",0.5),("w_labour_saving",0.0),("w_information",0.0),
                 ("w_novelty",0.0),("w_magic_fear",0.4),("w_religious_rigidity",0.3),
                 ("w_commerce",0.3),("bribability",0.4),("patronage_weight",0.6),
                 ("adaptation_rate",0.10)):
        c["values"].setdefault(k, d)
    return c


def load():
    with open(TREE) as source:
        tree = json.load(source)
    with open(PRICES) as source:
        prices = json.load(source)
    nodes = {n["id"]: n for n in tree["nodes"]}
    wages = {k: v["rate"] for k, v in prices["wage_rates_denarii_per_hour"].items()
             if not k.startswith("_")}
    goods = {k: v["p"] for k, v in prices["purchase_prices_denarii"].items()
             if not k.startswith("_")}
    for n in nodes.values():
        n["_labour_cost"] = sum(wages[t] * h for t, h in n["lab"].items())
        n["_material_cost"] = sum(goods[m] * q for m, q in n["mat"].items())
        n["_total_cost"] = n["_labour_cost"] + n["_material_cost"] + n["cap"]
        n["_hired_hours"] = sum(n["lab"].values())
    return tree, prices, nodes, wages, goods


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
    key = id(nodes)
    hit = _DESC_CACHE.get(key)
    if hit is not None and hit[0] == len(nodes):
        return hit[1], hit[2]
    index = {k: i for i, k in enumerate(sorted(nodes))}
    kids = {k: [] for k in nodes}
    for m in nodes:
        for p in nodes[m]["pre"]:
            if p in kids:
                kids[p].append(m)
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
            k, expanded = stack.pop()
            if expanded:
                m = 0
                for c in kids[k]:
                    m |= (1 << index[c]) | masks.get(c, 0)
                masks[k] = m
                continue
            if k in masks:
                continue
            stack.append((k, True))
            for c in kids[k]:
                if c not in masks:
                    stack.append((c, False))
    _DESC_CACHE[key] = (len(nodes), masks, index)
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
    n = nodes[k]
    out, seen = [], set()
    for p in n["pre"]:
        if p not in seen:
            seen.add(p)
            out.append(p)
    for grp in (n.get("req_any") or []):
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
    hp = {k: hard_pre(nodes, k) for k in keys}
    indeg = {k: 0 for k in keys}
    for k in keys:
        for p in hp[k]:
            if p in keys:
                indeg[k] += 1
    # Reverse index: for each key, the OTHER keys that name it as a hard
    # prerequisite, in sorted order - the same relative order `sorted(keys)`
    # would have visited them in, since it is a subsequence of that sort.
    dependents = {k: [] for k in keys}
    for m in sorted(keys):
        for p in hp[m]:
            if p in keys:
                dependents[p].append(m)
    ready = deque(sorted(k for k in keys if indeg[k] == 0))
    out = []
    while ready:
        k = ready.popleft()
        out.append(k)
        for m in dependents[k]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
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
        c = stack.pop()
        if c in need or c not in nodes:
            continue
        need.add(c)
        stack.extend(hard_pre(nodes, c))
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
    for k in order:
        n = nodes[k]
        own = max(n["yrs"], n["ph"] / 2000.0)
        pb, pc = 0.0, []
        for p in hard_pre(nodes, k):
            if p in best and best[p] > pb:
                pb, pc = best[p], chain[p]
        best[k] = pb + own
        chain[k] = pc + [k]
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
        bad = [g["node"] for g in goals if g.get("node") not in nodes]
        if bad:
            raise SystemExit("tech_tree.json meta.goals names nodes that do "
                             "not exist: %s" % ", ".join(bad))
    return goals


def goal_lookup(tree, node_id):
    """The goal_catalog entry for `node_id`, or None if it is not one of the
    named, selectable goals (an arbitrary node id is still a legal --goal
    for `path`/`plan` - see resolve_goal - it just has no menu entry)."""
    for g in tree["meta"].get("goals") or ():
        if g.get("node") == node_id:
            return g
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
        known = ", ".join(sorted(g["node"] for g in tree["meta"].get("goals") or ()))
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
    wc = n.get("win_condition") or {}
    metric, op, val = wc.get("metric"), wc.get("op"), wc.get("value")
    pct = "%d%%" % round((val or 0.0) * 100)
    tmpl = WIN_CONDITION_LABELS.get(metric)
    if tmpl:
        return tmpl % pct
    return "a measurement (%s %s %s) is met" % (metric, op, val)


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
