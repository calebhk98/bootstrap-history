"""Node id and name resolution: looking a technology up by id or by name, and the small graph queries - what depends on it, what it unlocks - built directly on the loaded tree."""

import collections, hashlib, json, math, os, random, re
from collections import defaultdict

from ..data import *          # the shared tables and loaders
from ..data import (ANNUAL_WAGE, TRADES_ABSENT, TRADE_NOTES, WAGES, closure,
                   critical_path, downstream_count, is_downstream, load, money_word,
                   topo_order, trade_family)
from ..fog import strip_self_play_advice

from ..core import Sim




# The real ids, and a case-folded index onto them. Built once: parse_typed has
# no Sim to ask and runs on every line a player types. One load(), not two -
# it re-reads both tree files from disk and re-derives every node's cost, and
# this file already pays that once per process for NODE_IDS; NODE_NAME_NORM
# below reuses the same dict rather than paying it again.
_NODES_ONCE = load()[2]
NODE_IDS = frozenset(_NODES_ONCE)
NODE_IDS_LOWER = {k.lower(): k for k in NODE_IDS}


def _norm_name(text):
    """Fold case and punctuation, so a typed name matches what the game
    printed however it was capitalised or punctuated.

    Every screen in this game prints the NAME ("Horizontal loom") and every
    command up to now took only the ID ("tex_horizontal_loom") - testers
    found that jarring often enough to say so in almost identical words. A
    player copying a name back exactly, in any case, with or without the
    comma a name like "Loom, treadle" carries, has to land on the same key.
    """
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


# NAMES ARE NOT UNIQUE THE WAY IDS ARE - the tree has several nodes called
# things like "Bronze casting" at different tiers - so this maps one
# normalised name onto every id that carries it, and resolution (below)
# decides whether that is one answer or a question back to the player.
# Built once, alongside NODE_IDS_LOWER, for the same reason: no Sim exists yet
# when a typed line first has to be read.
NODE_NAME_NORM = defaultdict(list)
for _nn_k, _nn_n in _NODES_ONCE.items():
    NODE_NAME_NORM[_norm_name(_nn_n["name"])].append(_nn_k)
del _nn_k, _nn_n


def _resolve_by_name(text):
    """Every id whose name matches `text`, case and punctuation folded.

    Exact match first, so that typing a name back verbatim - which is what a
    player does after reading it off `state` or `available` - always lands on
    every node that carries exactly that name, never something merely close
    to it. Failing that, a unique prefix or a distinctive (4+ character)
    substring works too, the same generosity `_did_you_mean` already gives an
    id typo, extended to names because a player cannot be expected to know
    that names, unlike ids, are not unique.
    """
    q = _norm_name(text)
    if not q:
        return []
    exact = NODE_NAME_NORM.get(q)
    if exact:
        return list(exact)
    if len(q) < 3:
        return []            # too short to mean anything as a name fragment
    prefix = [k for nm, ids in NODE_NAME_NORM.items() if nm.startswith(q) for k in ids]
    if prefix:
        return prefix
    if len(q) >= 4:
        return [k for nm, ids in NODE_NAME_NORM.items() if q in nm for k in ids]
    return []


def _downstream_of(k, nodes):
    """Everything that depends on this node, however far away, following hard
    prerequisites AND substitution groups alike.

    NOT closure(), which answers a different question. closure() is what you
    MUST have, so it follows `pre` only, and it has to: a req_any group is a
    list of alternatives and treating every option as required would balloon
    the goal's own prerequisite set with things nobody needs. But "what rests
    on this" is the reverse question, and there a substitution option counts,
    because something really would be harder or impossible without it. The
    chinampa read "TOTAL DOWNSTREAM: 0" while genuinely feeding terracing.
    """
    seen, stack = set(), [k]
    while stack:
        cur = stack.pop()
        for m in _unlocked_by(cur, nodes):
            if m not in seen:
                seen.add(m)
                stack.append(m)
    seen.discard(k)
    return seen


# REVERSE INDEX, BUILT ONCE PER TREE. _unlocked_by used to answer "who needs
# k" by scanning every one of the tree's 2,849 nodes and all their req_any
# groups, on EVERY call - and _downstream_of calls it once per node on the
# frontier of its walk, so one `why`/`path`/`available` could fire it
# thousands of times. Profiled on a fresh, unfogged rome_100ad game, a single
# `available` made 6,954 such calls and 23.7 million dict lookups for 11.3s
# of an 11.33s command. The fix: walk every node ONCE, appending it to the
# reverse-index bucket for each id in its own `pre` and each `req_any`
# group's `options`, so `_unlocked_by` becomes a dict lookup.
#
# CACHE KEYED ON id(nodes), WITH A STRONG REFERENCE TO nodes HELD ALONGSIDE
# THE INDEX. `nodes` is normally the one global tree, loaded once and never
# mutated afterward (a repo-wide grep for assignments into a node's "pre" or
# "req_any" - see the report accompanying this change - turns up only
# offline tree-authoring tools that run before the tree is ever loaded, plus
# two places in test_regressions.py that mutate a small synthetic dict, and
# both do it before that dict's first use, never after these functions have
# already seen it). The test suite DOES build many short-lived synthetic
# node dicts, though, and id() is only unique among currently-alive objects:
# once a small dict is garbage collected, a brand-new dict can legitimately
# be allocated at that same address. A cache of {id(nodes): index} alone
# would then hand the new dict a stale index built for a completely
# different tree. Storing `nodes` itself in the cache entry keeps that exact
# dict alive for as long as the entry lives, so its id cannot be recycled
# into a stale hit while the entry is still around - the collision this
# guards against is structurally impossible, not just unlikely.
_unlocked_by_cache = {}  # id(nodes) -> (nodes, {prereq_id: sorted[dependent_id]})


def _unlocked_by_index(nodes):
    entry = _unlocked_by_cache.get(id(nodes))
    if entry is not None and entry[0] is nodes:
        return entry[1]
    idx = {}
    for m, value in nodes.items():
        prereqs = set(value["pre"])
        for g in (value.get("req_any") or []):
            prereqs.update(g.get("options") or {})
        for p in prereqs:
            idx.setdefault(p, []).append(m)
    for lst in idx.values():
        lst.sort()
    _unlocked_by_cache[id(nodes)] = (nodes, idx)
    return idx


def _unlocked_by(k, nodes):
    """Everything that needs this node, whether hard or as one option of a
    substitution group. sorted() because a set of ids iterates in an order
    that depends on PYTHONHASHSEED - here, sorted once when the reverse
    index (see _unlocked_by_index above) is built, not on every call.

    Returns a fresh list, same as the old per-call scan did: the index's own
    bucket is shared across every caller and every future call for this `k`,
    so handing it out directly would let one caller's in-place edit corrupt
    what the next caller sees. list(...) is a cheap copy of a small
    dependents list, not another tree scan."""
    return list(_unlocked_by_index(nodes).get(k, []))


def _did_you_mean(k, nodes, limit=8, s=None):
    """Names close to what was typed.

    This was a plain substring test, so it helped with a truncation and not at
    all with a typo: one wrong character and the answer was the literal words
    "did you mean: no idea". Substring first, because a partial name is the
    common case and an exact prefix is a better guess than anything fuzzy, then
    difflib for the rest.
    """
    q = str(k).lower()
    near = [x for x in nodes if q in x.lower()]
    if len(near) < limit:
        import difflib
        for x in difflib.get_close_matches(q, list(nodes), n=limit, cutoff=0.6):
            if x not in near:
                near.append(x)
    # A word from the middle of a name is a real attempt too: "wheelbarrow"
    # should find fud_wheelbarrow even when the fuzzy score does not.
    # A SUBSTANTIAL word from the middle of a name is a real attempt too:
    # "wheelbarrow" should find lnd_wheelbarrow. Four characters minimum,
    # because matching on "fud" or "ag2" returns every node in the branch and
    # buries the one good answer under seven bad ones.
    if len(near) < limit:
        parts = [w for w in q.split("_") if len(w) >= 4]
        for x in nodes:
            if any(w in x.lower() for w in parts) and x not in near:
                near.append(x)
            if len(near) >= limit:
                break
    # NOT THROUGH THE FOG. `help fog` says in as many words that there is no
    # way to view the whole tree, and `path` is properly disabled - and then a
    # misspelling was answered out of the complete namespace. A weird-play
    # tester typed `why transistor` and was handed junction_transistor and
    # point_contact_transistor; `why vacuum`, `why steam` and `why
    # semiconductor` each dumped eight hidden ids, and they pointed out that
    # two-letter prefixes would reconstruct the entire tree. A suggestion is
    # still a statement about what exists.
    if s is not None and getattr(s, "fog", False):
        memo = {}
        near = [x for x in near if s.is_visible(x, _memo=memo)]
    return near[:limit]
