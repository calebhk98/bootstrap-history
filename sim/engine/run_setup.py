"""Run setup shared by the CLI, the planner and the path search: a dice-free rng, the fixed
hash seed it needs, and strategy loading with its dependency-order repair."""
import json, os, random, sys

from sim.engine.data import MODDIR, STRATS, closure, hard_pre, topo_order
from sim.engine.mods import get_ordered_mods
from sim.engine.mods_strategies import mod_strategy_path


# ----------------------------------------------------------------------------
# A DICE-FREE RNG, FOR --deterministic ON run/compare/play/agent.
#
# `path_search.py` built this first, to answer its own question - "does the
# planned order even get there with the dice off?" - see that module's
# docstring for the full argument (scarce trades, the capital trap, and why
# `--no-events` alone was never enough to ask it). It lives HERE, not there,
# because BOTH files need it and one of them has to be the one place it is
# actually defined: `path_search.py` already imports `load_strategy` and
# `topo_stable` from this module, so importing this the same way costs
# nothing, while the reverse - this module reaching into a standalone
# script's namespace - would tie every ordinary invocation of `run`/
# `compare`/`play`/`agent` to path_search.py's own module-load order for no
# reason. A second, independently-typed copy of the same class was the other
# option, and is exactly the duplication this project's own comments warn
# against elsewhere: two copies drift, and the drift is invisible until a fix
# lands in one and not the other.
# ----------------------------------------------------------------------------

class DetRNG(random.Random):
    """A seeded rng whose random() always returns 1.0.

    Every probability check anywhere in this engine is "< threshold" with
    threshold in (0, 1) - a project's own risk of failing outright
    (engine/projects.py `_complete`), the 3.5% yearly attrition roll, the 25%
    manumission roll, the fractional-headcount rounding in
    `labour.py:_stochastic_round`, and every dated hazard `society.py`'s
    `_shocks` rolls for (staff loss, a sack, and their own "does it come to
    nothing instead" counter-rolls) - so a draw of 1.0 is never below any of
    them: nothing fails, nobody dies, nothing is freed by luck, no hazard
    lands, every fraction rounds down. `randint`/`sample` are never reached in
    a run built this way (they sit behind `not self.founder_alive`, and a
    dice-free trial is always run with an immortal founder), so overriding
    `random()` alone is enough to make a whole run reproduce identically
    regardless of seed - the seed number itself stops mattering, which is the
    point: this is the world with the dice removed, not a world with better
    dice.

    NOT THE SAME THING AS `--no-events`, and deliberately independent of it.
    `--no-events` only silences DATED weather/plague/political hazards (this
    engine's `self.events` flag gating `_shocks` in core.py) and, alone,
    still leaves project-failure risk, attrition, manumission and stochastic
    rounding drawing from an ordinary seeded rng every time - see that flag's
    own help text, which says exactly this. This class is the other half: it
    changes how every roll comes out, not which code paths run. In practice,
    passing `--deterministic` without `--no-events` still ends up dice-free,
    because `_shocks` is itself built entirely from the same "< threshold"
    rolls this class always fails - but the two flags are kept separately
    documented rather than one silently implying the other, because a reader
    of `--no-events`'s own help text should not have to already know this
    class exists to understand what that flag alone does and does not do.
    """
    def random(self):
        return 1.0


def ensure_fixed_hash_seed(seed="0"):
    """A "deterministic" trial is not, unless this runs first.

    `DetRNG` makes every `random()` call return 1.0, which is exactly
    reproducible on its own - but CPython hashes strings differently in every
    process by default (`hash("machinist")` differs run to run unless
    `PYTHONHASHSEED` is fixed), and this engine has at least one documented
    site (core.py's own comment on `rng.sample(losable, ...)`) where walking
    a bare, unsorted `set` of ids would depend on that hash order - so a
    --deterministic run whose output depended on iteration order over some
    other such set
    would silently stop being reproducible process to process, for no reason
    a reader of a diff would ever see. `PYTHONHASHSEED` can only be set
    before the interpreter starts, not from inside an already-running one, so
    a process not launched with it fixed re-execs itself, once, with it set.
    Shared with `path_search.py`, which needs this exact same guarantee for
    its own dice-free search trials and imports this function for it rather
    than keeping a second copy - see that module's own docstring for the
    fuller account of why this matters and what was actually measured about
    it.
    """
    if os.environ.get("PYTHONHASHSEED") == seed:
        return
    env = dict(os.environ, PYTHONHASHSEED=seed)
    os.execvpe(sys.executable, [sys.executable] + sys.argv, env)


def strategy_file(name):
    """The strategy file for a name: the strategies folder, then an installed mod's, then a literal path."""
    path = os.path.join(STRATS, str(name) + ".json")
    if os.path.exists(path):
        return path
    return mod_strategy_path(name, get_ordered_mods(MODDIR)) or (str(name) if os.path.exists(str(name)) else path)


def load_strategy(name, nodes, goal):
    # A NAME OR A PATH. --save-winner writes a strategy file wherever you ask it
    # to, and there was no way to read one back: this looked only inside the
    # strategies directory for name + ".json", so the captured order of a run
    # that actually reached the goal could be written and never used.
    path = strategy_file(name)
    if os.path.exists(path):
        strategy_data = json.load(open(path))
        order = [node_id for node_id in strategy_data["order"] if node_id in nodes]
        # Everything the strategy did not name gets a sensible default ordering:
        # things the goal needs first, then cheapest first. Falling
        # back to alphabetical order made the simulation spend a century acquiring
        # ox carts before it touched a furnace.
        # FROM THE TREE, NOT SPELLED OUT HERE. This named the goal by hand, so
        # when the win condition moved from the 1947 point-contact device to the
        # 1951 junction transistor, the ordering that decides what an unnamed
        # node is worth would have gone on ranking against the old one for ever,
        # silently and with nothing failing.
        need = closure(nodes, goal)
        rest = [node_id for node_id in nodes if node_id not in order]
        rest.sort(key=lambda k: (k not in need, nodes[k]["_total_cost"], k))
        # STABILISE THE WHOLE THING TOGETHER, not the two halves separately.
        # Sorting `rest` on its own left 681 places where a node preceded its
        # own prerequisite, because a node in `rest` knows nothing about where
        # in `order` its prerequisites sit (and the strategy's own list is not
        # perfectly ordered either: soap_hard is listed before potash_soda,
        # which it needs). One pass over the concatenation keeps the strategy's
        # preference wherever it is legal and repairs it where it is not.
        full = topo_stable(nodes, order + rest)
        return strategy_data.get("label", name), full, set(strategy_data.get("bounties", []))
    if name == "topo":
        need = closure(nodes, goal)
        order = topo_order(nodes, need)
        return ("bare topological order to the goal",
                order + [node_id for node_id in topo_order(nodes) if node_id not in need], set())
    if name == "cheapest":
        order = sorted(nodes, key=lambda k: nodes[k]["_total_cost"])
        return "cheapest first", topo_stable(nodes, order), set()
    raise SystemExit("unknown strategy: %s" % name)


def topo_stable(nodes, preference, already=()):
    """Reorder `preference` so no node precedes its prerequisites, disturbing
    the given order as little as possible.

    `already`: nodes that are ALREADY ahead of this list and must count as
    placed. Omitting a node from `already` that is genuinely ahead of this
    list is a serious and completely invisible bug: if a strategy names
    some nodes explicitly and sorts everything else goal-critical-first,
    handing this function that remainder WITHOUT telling it about the
    explicit nodes means every node whose prerequisites live in the
    explicit list can never satisfy `all(p in placed)`, falls through to
    the bulk dump below, and loses its place entirely - a cheap,
    goal-critical node can end up hundreds of places later than it belongs,
    starving the optimizer of work it needed early.
    """
    placed = set(already)
    out = []
    pref = list(preference)
    # hard_pre, NOT nodes[k]["pre"]: this function decides the order the
    # engine actually receives, and a req_any group with exactly one real
    # option is a prerequisite, not a choice - reading `pre` alone here
    # could place a node like mat_bulk_steel ahead of mat_manganese even
    # though mat_bulk_steel cannot actually be built without it.
    hard_pre_by_node = {node_id: hard_pre(nodes, node_id) for node_id in pref}
    # Index the dependants so each placement only revisits what it could free,
    # rather than rescanning the whole list: a list.remove() inside a scan of
    # the whole list is O(n^2) over 2,700 nodes.
    waiting = {}
    ready = []
    for node_id in pref:
        missing = sum(1 for prereq_id in hard_pre_by_node[node_id] if prereq_id not in placed)
        waiting[node_id] = missing
        if not missing:
            ready.append(node_id)
    dependants = {}
    inset = set(pref)
    for node_id in pref:
        for prereq_id in hard_pre_by_node[node_id]:
            if prereq_id in inset:
                dependants.setdefault(prereq_id, []).append(node_id)
    rank = {node_id: i for i, node_id in enumerate(pref)}
    import heapq
    heap = [(rank[node_id], node_id) for node_id in ready]
    heapq.heapify(heap)
    seen = set()
    while heap:
        _rank, node_id = heapq.heappop(heap)
        if node_id in seen:
            continue
        seen.add(node_id)
        out.append(node_id)
        placed.add(node_id)
        for dependent_id in dependants.get(node_id, ()):
            waiting[dependent_id] -= 1
            if waiting[dependent_id] == 0 and dependent_id not in seen:
                heapq.heappush(heap, (rank[dependent_id], dependent_id))
    # Anything genuinely unreachable (a prerequisite outside both lists) keeps
    # its preferred order rather than being dropped.
    if len(out) < len(pref):
        out.extend(node_id for node_id in pref if node_id not in seen)
    return out
