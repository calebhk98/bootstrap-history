"""The tech tree itself, viewed through the protocol: why/available and node-explain, and the subject grouping they share."""

import hashlib

from ..data import closure, critical_path, downstream_count, is_downstream
from ..fog import strip_self_play_advice

from .nodes import _downstream_of, _unlocked_by
from .state import _waiting_on
from .ventures import _VENTURE_SUPERVISION_NOTE
# DEFAULT_AVAILABLE_LIMIT is NOT imported here: cli.py patches
# engine.protocol.DEFAULT_AVAILABLE_LIMIT directly at runtime, so
# _agent_available reads it through the protocol module itself, live -
# see _wrap's own comment on the same pattern, in engine/proto/util.py.

SUBJECTS = {
    "00": "the briefing", "01": "the world as it is", "03": "society and politics",
    "10": "metallurgy", "20": "chemistry", "30": "glass and optics",
    "40": "power and precision", "50": "electricity", "55": "semiconductors",
    "60": "mathematics and method", "70": "medicine and biology",
    "75": "agriculture and food", "76": "farming, in depth",
    "80": "printing and information", "85": "roads, bridges and canals",
    "86": "transport, in depth", "87": "construction", "88": "signals and media",
    "89": "the remaining arts", "90": "textiles", "91": "the household",
    "95": "expeditions", "96": "finance", "97": "military",
    "98": "power stations",
}


def _subject_of(n):
    """A readable heading for a node, from its knowledge module.

    There are 241 distinct `cat` values and 26 knowledge modules. The modules
    are the ones a person would recognise as subjects.
    """
    kb_code = (n.get("kb") or "").split("#")[0]
    return SUBJECTS.get(kb_code[:2], "everything else")


def _staff_short(n):
    """"2s1a" - the standing staff a project needs, in a table cell.

    Staffing has to be visible on the row itself, not only discoverable
    one node at a time through `why`: a project that looks startable by
    cost and hours can still be waiting on people, and two characters a
    trade is enough to see it while scanning.
    """
    bits = ""
    if n["sch"]:
        bits += "%gs" % round(n["sch"], 1)
    if n["art"]:
        bits += "%ga" % round(n["art"], 1)
    return bits or "-"


def _short_of_staff(s, n):
    """True when you could NOT staff this today. Marks the row with a *.

    THE SAME MEASURE start_reason USES: comparing against self.artisans
    alone, when the gate counts the founder's own hands and anything you
    have under contract, would mark a project as unstaffed while it
    starts and builds at full speed with nobody on the payroll at all. A
    marker that contradicts the gate it is describing is worse than no
    marker.
    """
    return bool(n["art"] > s.craft_hands_available() + 1e-9
                or n["sch"] > s.effective_scholars() + 1e-9)


def _staff_fields(s, n):
    """The two staff keys, present only when they SAY something.

    A row that needs nobody, or that you can already staff, carries neither.
    `available` has a size budget: forty bytes of "needs_staff":"-",
    "short_of_staff":false on every one of two hundred rows is eight
    kilobytes spent saying nothing.
    """
    out = {}
    short = _staff_short(n)
    if short != "-":
        out["needs_staff"] = short
        if _short_of_staff(s, n):
            out["short_of_staff"] = True
    return out


def _coarse_round(x):
    """Round a fogged revenue guess to a figure a person would actually say
    aloud - "three to five hundred a year", not "347.2 to 511.8 den/yr".
    Real-looking precision on a number that is, by construction, not the
    truth would read as measured rather than guessed, which defeats the
    point of guessing at all.
    """
    x = max(0.0, x)
    if x == 0:
        return 0.0
    step = 5 if x < 100 else 25 if x < 1000 else 100 if x < 10000 else 500
    return round(x / step) * step


def _revenue_known_exactly(s, k):
    """Have you actually RUN this long enough to know what it earns?

    Granted knowledge (k in s.granted) is answered True unconditionally: it
    is part of the persona you arrived with, not a prospect you are sizing
    up, so there is nothing to guess about. Anything else you have finished
    needs a few years of its own ledger behind it - "a few years" taken
    literally, three - before the figure stops being a forecast and starts
    being a fact; done_year missing (a bookkeeping gap, not a fresh
    completion) defaults to True rather than trapping a player in a fog
    the engine itself cannot explain.
    """
    if k not in s.done:
        return False
    if k in s.granted:
        return True
    started = s.done_year.get(k)
    if started is None:
        return True
    return (s.year - started) >= 3


def _fog_revenue_estimate(s, k):
    """What `available` and `why` show for EARNS/YR on a thing you have
    never run, under fog of war: a range, not the true figure.

    An exact payback figure under fog would let a player choose which side
    branches to build purely by reading a prospectus, without ever having
    worked out the tree - steering straight past the decisions fog exists
    to leave uncertain. Real payback is a thing you learn by running a
    concern for a few years, not by reading a number off a prospectus
    before you have so much as broken ground.

    Two things this must never be:
      - RE-ROLLED. A fresh call to self.rng here would answer differently on
        two consecutive looks at the same screen, and would also consume a
        draw from the SAME generator the simulation itself steps with - so
        merely asking `why` twice would change how the game plays out.
        Read-only commands must not touch self.rng. Instead this hashes
        something stable for the LIFE of one game (this civilisation, this
        goal, this starting purse) together with the node's own id, so the
        same game asked the same question twice gets the same answer, and a
        different game is not guaranteed to.
      - A TIGHT SYMMETRIC BAND ON THE TRUTH. "400 +/- 50" tells you 400 just
        as plainly as the bare number did, because the midpoint gives it
        away. The low and high bounds below are pulled by two independently
        drawn fractions, so the middle of the printed range is not, in
        general, anywhere near the real figure, and averaging the two bounds
        does not recover it.
    It DOES widen with how well this node's own numbers are attested: `conf`
    is already in the tree data for exactly this reason (A well attested, B
    probable, C the author's estimate), so a guess about a well-documented
    Roman trade is tighter than a guess about a Han institution nobody wrote
    down the takings of, the same as a historian's own uncertainty would be.
    """
    node = s.nodes[k]
    real = node["rev"]
    if real <= 0:
        return None          # nothing to estimate; a non-earner is a non-earner under fog too
    key = "%s|%s|%.1f|%s" % (s.civ.get("id") or s.civ.get("name") or "civ",
                             getattr(s, "goal", "") or "",
                             s.cfg.get("start_capital", 0.0), k)
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    half = {"A": 0.30, "B": 0.55}.get(node.get("conf"), 0.85)
    lo_frac = 0.35 + (digest[0] / 255.0) * 0.55
    hi_frac = 0.35 + (digest[1] / 255.0) * 0.90
    low = _coarse_round(real * (1.0 - half * lo_frac))
    high = _coarse_round(real * (1.0 + half * hi_frac))
    if high <= low:
        high = low + (5 if low < 100 else 25 if low < 1000 else 100)
    return [low, high]


def _brief(s, nodes, k, fog):
    """One row of `available`.

    Carries the numbers that actually decide whether to start a node: what
    it EARNS, what it costs every year afterwards, and how much else rests
    on it - not only cost, hours, years and risk. Those decisive numbers
    otherwise live only in `why`, one node at a time, forcing a player who
    wants to compare options to call `why` on every candidate by hand. An
    interface that hides its own decisive numbers turns competent play into
    writing a scraper.
    """
    node = nodes[k]
    # The SHORT band in a table row. `why` gets the long sentence, because it
    # is explaining one thing; a row is a row, and eleven copies of "nothing
    # else; this is worth having for itself" is half a kilobyte of a reply that
    # has a size budget to keep.
    rests = _rests_band(downstream_count(nodes, k)).split(";")[0]
    if fog:
        # A ROW HERE IS ALWAYS A THING YOU HAVE NOT BUILT - `available` lists
        # what you could BEGIN, never what you already have - so there is no
        # "have you run it long enough" case to check; see
        # _revenue_known_exactly for the one that `why` does need, because
        # `why` also answers for things you finished years ago.
        _est = _fog_revenue_estimate(s, k)
        return {"id": k, "name": node["name"],
                "cost": round(s.project_cost(k), 1),
                "your_hours": node["ph"],
                "least_years": node["yrs"],
                # effective_risk, NOT n["risk"]. Once a project has failed
                # once, retry learning means the tree's bare figure is no
                # longer what the dice use, and quoting it would understate
                # what a second attempt is worth.
                "chance_of_failure": s.effective_risk(k),
                # WHAT A FAILURE COSTS, not only how likely one is. A failure
                # takes a flat 40% of the money and sets 40% of the hours to
                # do again; the rate was on the screen and the sum never was,
                # so three players in a row read a single-digit risk as a
                # small thing and were not expecting what it took off a large
                # project. Zero when the work cannot fail, so nothing invents
                # a danger that is not there.
                "failure_costs": (round(s.project_cost(k) * 0.4, 1)
                                  if node["risk"] else 0.0),
                "failure_costs_hours": round(node["ph"] * 0.4, 1) if node["risk"] else 0.0,
                "earns_per_year": _est if _est is not None else round(node["rev"], 1),
                "costs_per_year_after": round(node["up"], 1),
                "how_much_rests_on_this": rests,
                **_staff_fields(s, node)}
    return {"id": k, "name": node["name"], "cat": node["cat"],
            **_staff_fields(s, node),
            "cost": round(s.project_cost(k), 1), "founder_hours": node["ph"],
            "calendar_floor_years": round(s.calendar_floor(k), 2),
            "nominal_calendar_floor_before_reputation": node["yrs"],
            "risk": s.effective_risk(k),
            "earns_per_year": round(node["rev"], 1),
            "costs_per_year_after": round(node["up"], 1),
            # _downstream_of, NOT downstream_count. The cached bitmask index
            # in data.py follows hard prerequisites only, and it must: adding
            # req_any options to it introduces real CYCLES (junction_transistor
            # -> silicon_path -> point_contact_transistor -> junction_transistor
            # is one of four), and a bitmask DFS that assumes a DAG runs out of
            # memory on them. The tree is acyclic on `pre` and is not acyclic
            # on `pre` plus substitutions. This walk carries a visited set, so
            # it is safe on the real graph, and it is the one place the number
            # is shown to a player as "nothing depends on this".
            "downstream_count": len(_downstream_of(k, nodes))}


def _full_entry(s, nodes, k, fog):
    entry = _brief(s, nodes, k, fog)
    node = nodes[k]
    if fog:
        entry["summary"] = s.fog_summary(k)
        if node["lab"]:
            entry["trades_needed"] = sorted(node["lab"])
    else:
        entry["prerequisites"] = node["pre"]
        # See strip_self_play_advice: a node's own note is data written by a
        # designer ranking it against the rest of the tree, not something the
        # founder in the story could know, and that stays cut whether or not
        # fog is on - see the block comment in fog.py.
        entry["note"] = strip_self_play_advice(node["note"])
    # THE HONEST TOTAL, not the risk and the floor left for the player to
    # multiply by hand - and only HERE, on the full per-node entry, not on
    # _brief's own compact digest rows (cheapest_six, most_rests_on_these):
    # those have their own reply-budget to keep inside, and this number is
    # worth a few extra bytes on the one
    # row you asked to actually look at, not on every row of a six-wide
    # sampler. See expected_calendar_years' own docstring (projects.py): it
    # is >= the floor above, strictly more once risk is above zero, and it
    # is why a 45%-risk, 4-year-floor node is not a 4-year project.
    if node.get("risk"):
        entry["expected_calendar_years_with_retries"] = round(
            s.expected_calendar_years(k), 2)
    return entry


# EVERY SORT A PLAYER MIGHT WANT, ONE TABLE, shared by both the paged
# `available` list and the "heard of but cannot begin" list under it, so a
# player only has to learn one vocabulary: {"cmd":"available","sort":"risk"}
# and the heard-of block below it sort the same way.
_SORT_KEYS = {
    "price": lambda s, n, k: s.project_cost(k),
    "cost": lambda s, n, k: s.project_cost(k),
    "hours": lambda s, n, k: n[k]["ph"],
    "years": lambda s, n, k: n[k]["yrs"],
    "earns": lambda s, n, k: n[k]["rev"],
    "revenue": lambda s, n, k: n[k]["rev"],
    "upkeep": lambda s, n, k: n[k]["up"],
    "risk": lambda s, n, k: n[k]["risk"],
    "alpha": lambda s, n, k: n[k]["name"].lower(),
    "alphabetical": lambda s, n, k: n[k]["name"].lower(),
    "name": lambda s, n, k: n[k]["name"].lower(),
    # FEWEST_MISSING: fewest of its OWN direct prerequisites still missing -
    # i.e. closest to becoming startable, never distance to whatever goal is
    # set. Every node in the STARTABLE list has zero missing by definition,
    # so this only discriminates the heard-of list; asking for it on the
    # startable list is harmless, not an error, and falls back to id order
    # there. `path <goal>` answers "what could I start today toward this
    # goal" without leaking the hidden tree; this key never measures that,
    # so it is named for what it actually measures rather than "near" or
    # "nearest", which could be misread as "nearest to your goal". Those two
    # names still work, for any script already using them, but do not
    # appear in the advertised list below.
    "fewest_missing": lambda s, n, k: sum(1 for prereq_id in n[k]["pre"] if prereq_id not in s.done),
    "near": lambda s, n, k: sum(1 for prereq_id in n[k]["pre"] if prereq_id not in s.done),
    "nearest": lambda s, n, k: sum(1 for prereq_id in n[k]["pre"] if prereq_id not in s.done),
}

_SORT_KEY_NAMES = ("price", "hours", "years", "earns", "upkeep", "risk",
                   "alpha", "fewest_missing")


def _available_params(cmd):
    """The query knobs off an `available` command, parsed once: the rest of
    the assembly reads want_subject, find, sort_by and so on as plain
    locals, instead of re-deriving each one from cmd at every point it is
    used.
    """
    # QUOTES ARE THE NATURAL INSTINCT for a subject with a space in it, and
    # `available "power and precision"` silently matched nothing while the
    # unquoted form worked. Strip them rather than failing quietly.
    want_subject = (cmd.get("subject") or cmd.get("group") or "").strip()
    want_subject = want_subject.strip('"\'').lower()
    find = (cmd.get("find") or cmd.get("search") or "").strip().strip('"\'').lower()
    show_all = bool(cmd.get("all"))
    try:
        limit = int(cmd.get("limit", 0))
    except (TypeError, ValueError):
        limit = 0
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    afford = float(cmd.get("afford")) if str(cmd.get("afford", "")).strip() not in ("", "None") else None
    sort_by = str(cmd.get("sort") or "").strip().lower()
    _sort_fn = _SORT_KEYS.get(sort_by)
    reverse = bool(cmd.get("reverse"))
    # PAGES THE HEARD-OF LIST, the same way `offset` pages the startable
    # one. Parsed here, once, rather than a second time down inside the fog
    # block: cmd does not change between the two reads, so parsing it once
    # instead of twice is not a behaviour change.
    try:
        heard_offset = max(0, int(cmd.get("heard_offset", 0)))
    except (TypeError, ValueError):
        heard_offset = 0
    return (want_subject, find, show_all, limit, offset, afford, sort_by,
            _sort_fn, reverse, heard_offset)


def _matches_find(nodes, find, k):
    """Match every query word across ids, names, anchors, and aliases."""
    aliases = nodes[k].get("aliases") or []
    if isinstance(aliases, str):
        aliases = [aliases]
    haystack = " ".join([k, nodes[k].get("name", ""),
                         nodes[k].get("kb", "")] + aliases).lower()
    terms = [term for term in find.replace("_", " ").split() if term]
    return bool(terms) and all(term in haystack for term in terms)


def _busy_subject_note(s, nodes, want_subject, fog):
    """THE SUMMARY COUNTED IT AND THE FILTER DID NOT. `available` listed
    "society and politics 1 1,200 1,200 1" and `available society and
    politics` answered "nothing in it", because the one item was already
    active. Say which, rather than appearing to disagree with the line
    above it.

    Returns the suffix to append to why_these, or "" when nothing in the
    subject is busy - so the caller can always append the result, the same
    as the original's `if _busy:` guard, just moved inside.
    """
    _busy = sorted(node_id for node_id in nodes
                   if want_subject in _subject_of(nodes[node_id]).lower()
                   and (node_id in s.active or node_id in s.done)
                   and (not fog or s.is_visible(node_id)))
    if not _busy:
        return ""
    return (" - nothing left to begin; you already have or "
            "are working on " + ", ".join(_busy[:4]))


def _select_startable(s, nodes, startable, fog, find, want_subject, afford):
    """Which startable nodes match the find/subject/afford filters the
    player asked for, and the reason to show under "showing" if any.
    """
    sel, why_these = startable, None
    if find:
        sel = [node_id for node_id in startable if _matches_find(nodes, find, node_id)]
        why_these = "matching %r" % find
    elif want_subject:
        sel = [node_id for node_id in startable if want_subject in _subject_of(nodes[node_id]).lower()]
        why_these = "in %r" % want_subject
        if not sel:
            why_these += _busy_subject_note(s, nodes, want_subject, fog)
    if afford is not None:
        sel = [node_id for node_id in sel if s.project_cost(node_id) <= afford]
    return sel, why_these


def _sort_startable_list(s, nodes, sel, _sort_fn, reverse):
    """Sort a page of startable nodes: the column the player asked for, or
    cost by default. Shared with the heard-of list below it, per the sort
    table's own docstring.
    """
    # SORT THE FULL SELECTION, THEN CUT: sorting only the current page after
    # cutting it from strategy order would show a cost-sorted view of an
    # arbitrary page's worth of nodes, not the true cheapest items overall.
    # DEFAULT COST, BUT NOT THE ONLY CHOICE: `sort` picks any column,
    # `reverse` flips it.
    if _sort_fn:
        return sorted(sel, key=lambda k: (_sort_fn(s, nodes, k), k), reverse=reverse)
    else:
        return sorted(sel, key=lambda k: (s.project_cost(k), k))


def _heard_all_sorted(s, nodes, find, want_subject, _sort_fn, reverse):
    """The full heard-of-but-not-startable list, filtered by the same
    find/subject the startable list used, sorted nearest-first (or by
    whatever column was asked for). Not yet paged; see _heard_of_block.
    """
    # CLOSEST FIRST, NOT ALPHABETICALLY: sorting by id and cutting at a page
    # size would always show the same handful of things beginning with a, b
    # and c, however many the player had heard of and however near the
    # rest were. Fewest missing prerequisites first is the order that
    # answers the question the list is actually asked: what is nearly
    # within reach?
    _heard_all = [node_id for node_id in getattr(s, "revealed", set())
                  if node_id not in s.done and node_id not in s.active
                  and not s.start_reason(node_id)[0]]
    # THE SAME SEARCH, OR NOTHING: filtered by the same `find`/`subject` a
    # player set on the startable list, not the usual nearest-first
    # regardless of what was typed. Ignoring the search here would dump
    # unrelated heard-of items under a heading that gives no sign any of it
    # is unrelated to the search - a search that matches nothing is
    # supposed to look like nothing, and a search that matches something
    # heard-of-but-not-yet-startable is exactly the case this list exists
    # to answer.
    if find:
        _heard_all = [node_id for node_id in _heard_all if _matches_find(nodes, find, node_id)]
    elif want_subject:
        _heard_all = [node_id for node_id in _heard_all
                      if want_subject in _subject_of(nodes[node_id]).lower()]
    # NEAREST-FIRST BY DEFAULT, but the same `sort`/`reverse` a player set
    # on the startable list applies here too - one vocabulary for both
    # halves of the screen, per the sort table's own docstring.
    if _sort_fn:
        _heard_all.sort(key=lambda k: (_sort_fn(s, nodes, k), k), reverse=reverse)
    else:
        _heard_all.sort(key=lambda k: (sum(1 for prereq_id in nodes[k]["pre"]
                                           if prereq_id not in s.done), k))
    return _heard_all


def _heard_of_block(s, nodes, fog, find, want_subject, _sort_fn, reverse, heard_offset):
    """The "heard of but cannot begin" list: closest first, searchable and
    pageable the same way the startable list is. Empty outside fog, where
    there is nothing hidden to report on.
    """
    heard, heard_more, heard_from = [], 0, 0
    if fog:
        _heard_all = _heard_all_sorted(s, nodes, find, want_subject, _sort_fn, reverse)
        # PAGEABLE, and it says when it is cut: a silent slice at 25 with no
        # note that it was truncated leaves a large heard-of list with no
        # way to see the rest. `heard_offset` pages it, the same way
        # `offset` pages the startable list.
        heard = _heard_all[heard_offset:heard_offset + 25]
        heard_more = max(0, len(_heard_all) - heard_offset - len(heard))
        heard_from = heard_offset
    heard_block = [{"id": node_id, "name": nodes[node_id]["name"],
                    "why_not": s.start_reason(node_id)[1]} for node_id in heard]
    return heard_more, heard_from, heard_block


def _list_page(s, nodes, sel, startable, why_these, fog, show_all, offset, limit,
               DEFAULT_AVAILABLE_LIMIT):
    """The page itself, and the "nothing matched" message when it is empty.
    Returns (out, page) - out is the reply built so far, page is the slice
    of `sel` actually shown, which the caller needs again for paging hints.
    """
    # DEFAULT_AVAILABLE_LIMIT, NOT A BARE NUMBER: a player can raise it from
    # the Options screen - see its own comment, near TYPED_HINTS - instead
    # of typing limit:N by hand on every page of a long search or subject
    # list.
    page = sel if show_all else sel[offset:offset + (limit or DEFAULT_AVAILABLE_LIMIT)]
    out = {"ok": True, "count": len(sel), "of_everything_startable": len(startable),
           # The same figure the digest carries, so a paged list can mark
           # what you could not raise today. See _cost_marker.
           "you_could_raise_for_a_project": round(s.spending_power("start"), 1),
           "showing": ("nothing%s" % ((" " + why_these) if why_these else "")
                       if not page else
                       "%d-%d%s" % (offset + 1, offset + len(page),
                                    (" " + why_these) if why_these else "")),
           "available": [_full_entry(s, nodes, node_id, fog) for node_id in page]}
    if not page:
        # "1-0 matching 'furnace'" over an empty table is a range that
        # cannot exist, printed where an answer should be. Say the answer
        # instead - and, under fog, say only what a player is entitled to
        # know: that nothing they can begin TODAY matches. Whether the
        # thing exists at all in the tree is exactly what fog withholds.
        # SAY WHAT IT SEARCHED: an empty result could otherwise read as the
        # search ignoring ids, when it searches both ids and names, and
        # only among what is startable NOW.
        out["nothing_matched"] = (
            "Nothing you could begin today matches that. This looks at both "
            "ids and names, but only among what you could start now."
            + (" That does not mean there is no such thing; it means "
               "nothing in front of you right now answers to it. Try a "
               "shorter word, or a subject: 'available metallurgy'."
               if fog else
               " Try a shorter word, or a subject: 'available metallurgy'."))
    return out, page


def _list_sort_and_paging_hints(out, sel, page, show_all, offset, sort_by, _sort_fn, reverse):
    """DISCOVERABLE, not just possible. `help available` says this too, but
    a naive player reading the table itself should not have to go looking
    for the one line that explains how to change what they are looking at.
    Mutates `out` in place.
    """
    out["sorted_by"] = sort_by if _sort_fn else "cost"
    if reverse:
        out["sorted_by"] += ", reversed"
    out["to_sort_or_page_differently"] = (
        "add a 'sort' of %s, and 'reverse' to flip it; 'offset'/'limit' "
        "page the list you could start, 'heard_offset' pages the "
        "heard-of one below it - all the way to the end."
        % ", ".join(_SORT_KEY_NAMES))
    if not show_all and offset + len(page) < len(sel):
        out["more"] = ('%d more; ask again with "offset": %d'
                       % (len(sel) - offset - len(page), offset + len(page)))


def _list_heard_hint(out, fog, heard_block, heard_more, heard_from, offset, sort_by, _sort_fn, reverse):
    """The heard-of block under a paged list - only on the first page
    (offset == 0). Mutates `out` in place.
    """
    if fog and heard_block and offset == 0:
        out["heard_of_but_cannot_begin"] = heard_block
        if heard_more:
            out["and_more_you_have_heard_of"] = (
                "%d more, %s; ask again with heard_offset %d"
                % (heard_more,
                   ("sorted by %s%s" % (sort_by, " reversed" if reverse else ""))
                   if _sort_fn else "fewest missing prerequisites first, "
                                    "which is not the same as nearest to "
                                    "your goal",
                   heard_from + len(heard_block)))


def _list_reply(s, nodes, sel, startable, why_these, fog, show_all, offset, limit,
                 DEFAULT_AVAILABLE_LIMIT, sort_by, _sort_fn, reverse,
                 heard_block, heard_more, heard_from):
    """The paged reply: a subject, a search, an explicit page, or everything.
    """
    out, page = _list_page(s, nodes, sel, startable, why_these, fog, show_all,
                            offset, limit, DEFAULT_AVAILABLE_LIMIT)
    _list_sort_and_paging_hints(out, sel, page, show_all, offset, sort_by, _sort_fn, reverse)
    _list_heard_hint(out, fog, heard_block, heard_more, heard_from, offset, sort_by, _sort_fn, reverse)
    return out


def _digest_subject_rows(s, nodes, startable):
    """The subjects table: how many things, cheapest, dearest, and how
    many you could pay for, in each subject with something startable in
    it. Returns (rows, purse).
    """
    groups = {}
    for node_id in startable:
        group = groups.setdefault(_subject_of(nodes[node_id]), [])
        group.append(node_id)
    # The AFFORD column is about STARTING work, so it uses the rule `start`
    # uses. It used the purchase rule, which is why the hint under the table
    # offered "available afford 1,083" for a player `start` would have let
    # commit 1,767. See Sim.spending_power.
    purse = s.spending_power("start")
    rows = []
    for name, node_ids in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        costs = sorted(s.project_cost(node_id) for node_id in node_ids)
        rows.append({"subject": name, "things": len(node_ids),
                     "cheapest": round(costs[0], 1),
                     "dearest": round(costs[-1], 1),
                     "you_could_pay_for": sum(1 for cost in costs if cost <= purse)})
    return rows, purse


def _digest_leverage_and_cheap(s, nodes, startable):
    """The leverage column (most rests on these) and the cheapest six,
    deduplicated against each other. Returns (leverage, cheap).
    """
    # LEVERAGE FIRST, then price: deduplicating the other way round - the
    # leverage list dropping anything also in the cheapest six - would hide
    # exactly the nodes that matter most, since the spine of this game is
    # precisely the nodes that are BOTH: free, zero-revenue, and holding up
    # an age. Being cheap is the reason they are easy to miss, not a reason
    # to hide them from the column that exists to find them.
    _lev_all = sorted(startable, key=lambda k: (-downstream_count(nodes, k),
                                         s.project_cost(k)))
    # Keep the default reply below its readability budget. Five leverage rows
    # and six cheap rows crept over 6 KB as the explicit opening states grew;
    # four and five still expose both rankings without making the digest a page.
    leverage = _lev_all[:4]
    cheap = [node_id for node_id in sorted(startable, key=lambda k: s.project_cost(k))
             if node_id not in leverage][:5]
    return leverage, cheap


def _digest_stack_caution(s, leverage):
    """SAID ONCE, THE FIRST TIME THIS LIST IS EVEN LOOKED AT - not on every
    `available`, which would bury it in noise by the tenth call. "MOST
    RESTS ON THESE" is the one piece of unprompted advice this screen
    gives a brand-new player, and reads naturally as "start these" -
    which invites starting two or three of the leverage items together on
    turn one. Each one is priced correctly and honestly on ITS OWN `why`
    screen; almost none of them earn anything even once finished and
    opened (see earns_per_year on the rows above), and a poor_scholar's
    opening capital does not cover two or three of them at once. That is
    not a reason to stop recommending them - they really are the spine
    of the tree - it is a reason to say, in the same breath, that they
    add up.

    Returns the caution text the first time leverage is non-empty for
    this game, None afterward - the same one-shot guard the original's
    inline check kept on s._said_stack_caution, moved here with it.
    """
    if not leverage or getattr(s, "_said_stack_caution", False):
        return None
    s._said_stack_caution = True
    # SHORT ON PURPOSE - this reply has a byte budget (see the "wall of
    # text" check) and 'start' itself carries the full explanation once
    # it actually matters (its own "total_committed_across_active_work"
    # field). This is the pointer, not the essay.
    return ("each is priced fairly alone; most earn nothing even opened. "
            "'start' warns with your real total once stacking is unsafe.")


def _digest_heard_hint(out, fog, heard_block, heard_more, heard_from):
    """The heard-of block under the digest. Mutates `out` in place."""
    if fog and heard_block:
        out["heard_of_but_cannot_begin"] = heard_block
        if heard_more:
            out["and_more_you_have_heard_of"] = (
                'ask again with {"cmd":"available","heard_offset":%d} for %d '
                "more, fewest missing prerequisites first (not nearest to "
                "your goal - see 'path <goal>' for that, once fog is off)"
                % (heard_from + len(heard_block), heard_more))


def _digest_reply(s, nodes, startable, fog, DEFAULT_AVAILABLE_LIMIT,
                   heard_block, heard_more, heard_from):
    """The reply when nothing more specific was asked for."""
    # DEFAULT: the digest.
    rows, purse = _digest_subject_rows(s, nodes, startable)
    leverage, cheap = _digest_leverage_and_cheap(s, nodes, startable)
    # AND THE FOUR MOST RESTS ON: the spine of the whole game is a handful
    # of cheap, zero-revenue, tier-0 nodes - units_standards,
    # identity_cover, patron_local, workshop_first - which look like
    # nothing when the digest is sorted by price, the one axis that hides
    # them. Without a leverage column here, finding them means scripting
    # a `why` call for every startable id. Leverage is a column the game
    # already knows.
    out = {"ok": True, "count": len(startable),
           "showing": "a summary by subject, because the full list is %d things"
                      % len(startable),
           "subjects": rows,
           # _brief for a DIGEST. _full_entry carried each node's prerequisites
           # and full note - several hundred bytes apiece that the table never
           # renders and that `why` exists to give you properly. The digest's
           # job is to help you choose which `why` to run, and it has a size
           # budget precisely so that it stays a digest.
           "cheapest_six": [_brief(s, nodes, node_id, fog) for node_id in cheap],
           # _brief, not _full_entry: the table renders only the columns, and a
           # second block of fog summaries pushed the reply past the size a
           # reply is allowed to be. See the wall-of-text check.
           "most_rests_on_these": [_brief(s, nodes, node_id, fog) for node_id in leverage],
           "to_see_more": {
               "one subject": '{"cmd":"available","subject":"metallurgy"}',
               "by name": '{"cmd":"available","find":"furnace"}',
               "what you can pay for": '{"cmd":"available","afford":%d}' % int(max(0, purse)),
               "a page of everything": ('{"cmd":"available","limit":%d,"offset":0}'
                                        % DEFAULT_AVAILABLE_LIMIT),
               "all of it at once": '{"cmd":"available","all":true} (large)'},
           "you_could_raise_for_a_project": round(purse, 1)}
    _caution = _digest_stack_caution(s, leverage)
    if _caution:
        out["stacking_several_is_the_trap"] = _caution
    _digest_heard_hint(out, fog, heard_block, heard_more, heard_from)
    if fog:
        out["note"] = ("Under fog you see only what you could begin now, and things "
                       "you have heard of. There is no way to see the whole tree.")
    return out


def _agent_available(s, nodes, cmd=None):
    """What you could begin today.

    The default is a digest by subject, not everything: returning every
    startable entry in one reply produces hundreds of entries and well over
    a hundred kilobytes even early in a run - too much for a machine to
    make sense of, let alone a person. Ask for the part you want.
    """
    cmd = cmd or {}
    # LIVE, NOT A SNAPSHOT: cli.py's _apply_display_prefs patches
    # engine.protocol.DEFAULT_AVAILABLE_LIMIT directly (a module attribute,
    # not a call) - see that name's own comment in engine/proto/util.py.
    # Reading it back through the protocol module itself, instead of a
    # plain name this file would otherwise bind at import time, is what
    # makes that patch visible here.
    from .. import protocol as _protocol
    DEFAULT_AVAILABLE_LIMIT = _protocol.DEFAULT_AVAILABLE_LIMIT
    fog = getattr(s, "fog", False)
    # ONE memo for the whole sweep, not one per node. Under fog, checking
    # whether a deep node can start asks whether each of its missing
    # prerequisites is even visible, which asks the same question about
    # THEIR missing prerequisites, and neighbouring nodes in `order` share
    # most of that ancestry. Recomputing it fresh per node, 2,800 times, is
    # what made a single `available` call under fog on norse_900ad take
    # upward of a minute; sharing the memo across the sweep makes it once
    # per node actually touched. See is_visible()'s docstring.
    _memo = {}
    startable = [node_id for node_id in s.order if s.can_start(node_id, _memo=_memo)]

    # Split into one function per concern - parsing the query, selecting and
    # sorting the startable nodes, building the heard-of block, and
    # assembling either the paged list or the digest - with this function
    # left as the assembler. Every branch, sentence and ordering below lives
    # in the piece that owns it; nothing here decides anything the pieces
    # did not already decide.
    (want_subject, find, show_all, limit, offset, afford, sort_by,
     _sort_fn, reverse, heard_offset) = _available_params(cmd)

    sel, why_these = _select_startable(s, nodes, startable, fog, find, want_subject, afford)

    # THE SAME CONDITION GOVERNED SORTING AND WHICH REPLY TO BUILD, written
    # out twice in the original function with nothing between the two
    # copies that could change find/want_subject/limit/offset/show_all/
    # afford - the heard-of block below reads them but does not set them.
    # One name for it here, used at both points, changes nothing about
    # when the sort or the list branch actually run.
    wants_list = bool(find or want_subject or limit or offset or show_all
                       or afford is not None)
    if wants_list:
        sel = _sort_startable_list(s, nodes, sel, _sort_fn, reverse)

    heard_more, heard_from, heard_block = _heard_of_block(
        s, nodes, fog, find, want_subject, _sort_fn, reverse, heard_offset)

    # A LIST was asked for: a subject, a search, an explicit page, or everything.
    if wants_list:
        return _list_reply(s, nodes, sel, startable, why_these, fog, show_all,
                            offset, limit, DEFAULT_AVAILABLE_LIMIT, sort_by,
                            _sort_fn, reverse, heard_block, heard_more, heard_from)

    return _digest_reply(s, nodes, startable, fog, DEFAULT_AVAILABLE_LIMIT,
                          heard_block, heard_more, heard_from)


def _rests_band(n):
    """How much rests on a node, in the words a person in the year 100 could
    actually use. The exact count is a fog spoiler; the band is not.

    "NOTHING ELSE" HAS TO MEAN ZERO: the bottom band must cover only n == 0,
    never a wider range such as 0 to 3, or a node with real dependents gets
    described as having none - `why met_ore_crushing_sorting` could then
    say "nothing else rests on this" while met_jigging_gravity, sitting
    visible in the same list, gives "missing prerequisites:
    met_ore_crushing_sorting", contradicting itself inside a minute of
    ordinary play. Banding is the right answer to the spoiler problem,
    since the exact count is a map of the tree; a band whose words are
    false is not. Vague is allowed here, wrong is not - so 1 to 3 gets its
    own rung and the bottom one means what it says.
    """
    return ("almost everything" if n > 1200 else
            "a great deal" if n > 300 else
            "a fair amount" if n > 40 else
            "a few things" if n > 3 else
            "a little" if n > 0 else
            "nothing else; this is worth having for itself")


def _explain_identity(s, nodes, k, node):
    """Name, note, hours and the raw labour/material bills - the parts of
    `why` that need nothing computed, only read off the node and fog-
    scrubbed where the tree itself says a field can leak.
    """
    return {
        "id": k, "name": node["name"], "cat": node["cat"], "confidence": node["conf"],
        # See strip_self_play_advice (fog.py): drops any sentence that ranks
        # this node against the game or the tree itself - "the pivot of the
        # entire game", "THE highest expected-value node in the tree" - and
        # keeps everything else the note says. Applied here, not only under
        # fog: telling a player outright which of their own choices is
        # correct is the game answering its own question either way.
        "note": strip_self_play_advice(node["note"]),
        # FOG-SCRUBBED: the knowledge-base citation is a section anchor into
        # a shared markdown file, and the tree's own convention names most
        # anchors after the node id they document - so "kb":
        # "...#ag2_norfolk_course" on a completely unrelated, visible node
        # names a hidden node's id in plain sight, the same class of leak
        # `bounty` had with a raw prerequisite list. The generic fog
        # scanner in test_regressions.py exists to catch exactly this
        # class of leak on future commands too. fog_scrub is the one
        # filter every such free-text field goes through.
        "kb": s.fog_scrub(node["kb"]),
        "founder_hours": node["ph"],
        # Two different kinds of people: hired_labour is HOURS OF A JOB,
        # bought from whoever does that trade here, for this project only.
        # staff_needed is PEOPLE ON YOUR OWN BOOKS who understand your
        # methods and stay afterwards. They can name different trades
        # without contradicting each other, because they are not the same
        # question.
        "hired_labour": node["lab"],
        "materials": node["mat"],
    }


def _explain_cost(s, nodes, k, node):
    """The cost breakdown: base cost, every factor project_cost multiplies
    in, and what is left to pay if money is already sunk into this node.
    """
    # THE QUOTE MUST MATCH THE CHARGE: step() bills the base cost multiplied
    # by this society's domain factor and by how far it sits from the
    # material's source, so quoting the bare base cost here (identical for
    # every civilization) would make `why` compare two civilizations as
    # byte-identical when what they are actually charged differs - a player
    # plans against the quote, so the quote must not lie about it.
    return {"labour": round(node["_labour_cost"], 1),
                 "materials": round(node["_material_cost"], 1),
                 "capital": node["cap"],
                 "base_total": round(node["_total_cost"], 1),
                 "civ_domain_factor": round(s.civ_cost_factor(k), 3),
                 "material_distance_factor": round(s.material_cost_factor(k), 3),
                 # THE SCARCITY PREMIUM: project_cost multiplies this in, so
                 # the breakdown must list it too - what the market charges
                 # for a material it barely sells. Same lesson as
                 # price_index below - a breakdown that omits a factor
                 # project_cost actually uses is worse than no breakdown,
                 # because it invites a player to multiply the shown
                 # factors out and then fails that check.
                 "scarce_material_premium": round(s.material_market_factor(k), 3),
                 "opposition_factor": round(s.opposition_factor(k), 3),
                 # THE FACTOR ACTUALLY MULTIPLIED IN, not a decoy:
                 # project_cost multiplies by cost_money_factor()
                 # (price_index), so this field must report THAT, not
                 # money_real. Reporting money_real here would print 1.0 for
                 # a civilization whose prices actually run 1.4x Roman, and
                 # hide the breakdown's largest term - a breakdown offered
                 # as the explanation of a total has to reconcile with it,
                 # or it is worse than no breakdown.
                 "price_index": round(s.cost_money_factor(), 3),
                 "purchasing_power_of_the_coin": round(s.money_real, 3),
                 # The same figure the project will be billed, and must actually
                 # have paid in full before it can complete.
                 "total": round(s.project_cost(k), 1),
                 # AS OF TODAY: this total moves with prices, the coinage,
                 # what a material costs to get and what you have since
                 # built, so the same node quoted today and started years
                 # later can be billed a different amount - both figures
                 # are correct on their own day. The bill is fixed at the
                 # moment you START, and `start` says what it was fixed at.
                 "as_of_year": s.year,
                 "note": "today's price. It is fixed when you start, not when "
                         "you read it: quotes move with prices, the coinage "
                         "and what a material costs to get.",
                 # THE STICKER PRICE IS NOT WHAT `start` WOULD ACTUALLY
                 # CHARGE, once money is already sunk into this node:
                 # start_project's own _paid_now discount (see that
                 # function) subtracts paid_towards[k] before billing a
                 # single denarius, for a project a creditor or the
                 # player's own `stop` had halted partway. `why` must show
                 # that discounted figure too, or a player planning from it
                 # is planning against a number the engine would never
                 # actually charge.
                 **({"already_paid_towards_this": round(
                        min(s.project_cost(k),
                            max(0.0, getattr(s, "paid_towards", {}).get(k, 0.0))), 1),
                     "what_start_would_actually_charge": round(
                        max(0.0, s.project_cost(k)
                            - min(s.project_cost(k),
                                  max(0.0, getattr(s, "paid_towards", {}).get(k, 0.0)))), 1),
                     "why_less_than_the_total_above":
                        "this much was already paid in before the work "
                        "stopped, halted by a creditor or by your own "
                        "'stop'; it stands to your credit and comes off "
                        "the bill the moment you start this again"}
                    if k not in s.done and k not in s.active
                    and max(0.0, (getattr(s, "paid_towards", {}) or {}).get(k, 0.0)) > 0.5
                    else {})}



def _explain_revenue(s, nodes, k, node):
    """Upkeep (exact, even under fog) and revenue (fogged, unless this is
    granted knowledge or has been run long enough to know), plus what a
    practice of your own actually pays versus the tree's organised-concern
    figure.
    """
    return {
        # UPKEEP STAYS EXACT, EVEN UNDER FOG, AND REVENUE DOES NOT. Upkeep is
        # closer to a quoted PRICE than to a forecast - rent, wages and
        # materials are things you can ask around about before you commit,
        # the same way `cost` above is already shown exact and fixed the
        # moment you start. Revenue is different in kind: it is what the
        # market will actually pay for a thing nobody here has ever sold,
        # and that is not knowable in advance whatever you ask around, which
        # is the whole of the user's original question - "shouldn't the
        # payback be something you don't know until after research?" So
        # revenue alone is fogged; see _fog_revenue_estimate.
        "upkeep": node["up"],
        "revenue": (node["rev"] if (not getattr(s, "fog", False)
                                 or _revenue_known_exactly(s, k))
                   else (_fog_revenue_estimate(s, k) or 0.0)),
        "revenue_forecast_scope": (
            "Direct concern revenue only. Institutions may also increase "
            "household capacity, reachable staff, practice output, or other "
            "indirect income; those variable effects are not included here. "
            "Compare 'money' before and after opening."
            if k in s.CAPABILITY_INSTITUTIONS else None),
        # WHAT IT PAYS YOU, which for something in your own practice is a
        # third of the figure above: the tree quotes the trade as an
        # organised concern, and one person in a rented room is not one,
        # so both figures have to be shown or the plain revenue figure
        # overstates practice income threefold.
        "but_it_pays_YOU": (
            round(node["rev"] * s.PRACTICE_SHARE * s.practice_attention(), 1)
            if k in s._practice_set() and node["rev"] else None),
        "because": ("this is your own practice, not a concern: it pays about a "
                    "third of what the tree quotes for the trade, and selling "
                    "your hours for wages takes another bite"
                    if k in s._practice_set() and node["rev"] else None),
    }


def _explain_timing_and_risk(s, nodes, k, node):
    """The calendar floor, the risk, the expected years with retries
    counted in, and what a failure actually costs.
    """
    return {
        "calendar_floor_years": round(s.calendar_floor(k), 2),
        "nominal_calendar_floor_before_reputation": node["yrs"],
        "risk": s.effective_risk(k),
        # THE EXPECTED TOTAL, RETRIES INCLUDED - not the floor and the risk
        # left for the player to combine by hand. A 45%-risk, 4-year-floor
        # node is not a 4-year project: the bare geometric series 1/(1-p) is
        # 1.82 attempts, and even that understates it once retry learning
        # (RETRY_RISK_FLOOR/DECAY, RETRY_CALENDAR_CAP/DECAY - see
        # expected_calendar_years' own docstring in projects.py) starts
        # moving both the odds and the wait on every attempt after the
        # first. This must be computed through the SAME retry rule
        # _complete actually applies, not a second, looser approximation of
        # it, or the number told to a player before the dice start rolling
        # understates what a run of failures will actually cost.
        "expected_calendar_years_with_retries": round(
            s.expected_calendar_years(k), 2),
        # WHAT THE FAILURES SO FAR HAVE BOUGHT, said out loud, because a
        # number that quietly improves is a number a player cannot plan with.
        "attempts_already_failed": int(getattr(s, "failed_attempts", {}).get(k, 0)),
        "risk_before_any_attempt": node["risk"],
        # THE SUM, NOT ONLY THE RATE. See _node_explain's own note: a failure
        # takes a flat 40% of the money and puts 40% of the hours back on the
        # slate, and a player deciding whether to risk it is holding the size
        # of the project in their head, not the percentage.
        "failure_costs": round(s.project_cost(k) * 0.4, 1) if node["risk"] else 0.0,
        "failure_costs_hours": round(node["ph"] * 0.4, 1) if node["risk"] else 0.0,
    }


def _staffing_build_crew(s, node):
    """staff_needed, you_have, and the two "more than you have" warnings -
    the BUILD crew start_project gates on.
    """
    return {
        "staff_needed": {"scholars": node["sch"], "artisans": node["art"]},
        # THE FIGURE THE GAME ACTUALLY TESTS: start_project gates artisans on
        # craft_hands_available() - staff, plus yourself, plus any hours you
        # have already bought - not on s.artisans alone, which is only the
        # first of the three. Printing s.artisans here would show a number
        # that disagrees with the one that actually decides whether a
        # player can begin. Print what decides it.
        "you_have": {"scholars": round(s.effective_scholars(), 1),
                     "artisans": round(s.craft_hands_available(), 1)},
        "you_have_counts": ("counting yourself, and hours you have bought"
                            if s.founder_alive else "counting hours you have bought"),
        # SAY WHEN THE STAFF IT WANTS IS MORE THAN THIS SOCIETY HAS: a
        # society's literacy-driven hiring ceiling can be lower than what
        # the goal itself needs, and finding that out only in a late-game
        # refusal is too late to plan around.
        # AGAINST WHAT YOU ACTUALLY HAVE, not against the hiring ceiling
        # alone: a school and an academy grant scholars outright, on top
        # of anyone you could hire, so printing "literacy here will never
        # supply more than 6.4" beside a much larger actual headcount
        # would read as a hard block when it is not one.
        "more_scholars_than_this_society_can_supply": (
            "%s wanted; you have %.1f and literacy here will never let you HIRE "
            "more than %.1f. Printing, paper, schools and academies raise both."
            % (node["sch"], s.effective_scholars(), s.literate_capacity("scholar"))
            if (node["sch"] > s.literate_capacity("scholar")
                and node["sch"] > s.effective_scholars()) else None),
        "more_craftsmen_than_your_household_can_hold": (
            "%s wanted; you have %.1f and could hold %.1f in all. %s"
            % (node["art"], s.artisans,
               s.headcount() + max(0.0, s.household_room()), s._room_advice())
            if (node["art"] > s.headcount() + max(0.0, s.household_room())
                and node["art"] > s.artisans) else None),
    }


def _staffing_standing_crew(s, _is_venture, _sup_sch, _sup_art, _free_sch, _free_art,
                             _foreman_trade, _foreman_fte):
    """staff_to_keep_it_open and the rest of the venture-supervision
    fields - the STANDING crew `open` actually checks, a separate and
    often smaller (sometimes larger) figure from the build crew above.
    """
    return {
        # A SECOND STAFF FIGURE, AND IT IS NOT THE SAME NUMBER. staff_needed
        # above is the BUILD crew - what start_project gates on, and what
        # goes idle again once the work is finished. A going concern is a
        # standing commitment on top of that: somebody of yours has to keep
        # an eye on it every year it runs, which is venture_hands() - a
        # quarter of the build crew, floored by how much the concern takes
        # in (see venture_hands's own comment) - and open_venture() is the
        # ONLY other place this is checked. Three players built something on
        # the strength of the number above, paid for it in full, and were
        # then refused at `open` on a bigger number neither `why` nor
        # `available` had ever shown them - one measured it exactly:
        # "2.13 craftsmen" enforced against a `why` that had said "2
        # artisans" and nothing else. Read the SAME function open_venture()
        # calls, not a second estimate of it, so the two can never drift
        # apart again.
        "staff_to_keep_it_open": (
            {"scholars": round(_sup_sch, 2), "artisans": round(_sup_art, 2)}
            if _is_venture else None),
        "specialist_foreman_to_keep_it_open": (
            {"trade": _foreman_trade, "fte": round(_foreman_fte, 2),
             "free_now": round(s.venture_foreman_free(_foreman_trade), 2)}
            if _foreman_trade else None),
        "staff_to_keep_it_open_means": (
            "a SEPARATE requirement from staff_needed above, and the one "
            "'open' actually enforces once this is built: a continuous "
            "SHARE of your own people's time spent watching it every year "
            "it runs, not a headcount and not the crew that built it. "
            "Often smaller than staff_needed - typically a quarter of it "
            "- but a concern that takes in a great deal needs more "
            "watching than it took to build, and this can come out "
            "LARGER. Checked when you 'open' it, not when you 'start' it, "
            "so know this number before you spend money on the other one."
            if _is_venture else None),
        # "2.13 craftsmen" IS NOT A HEADCOUNT - SAY SO RIGHT WHERE IT IS
        # SHOWN, not only in a help topic nobody thought to ask for. See
        # _VENTURE_SUPERVISION_NOTE's own comment for the exact complaint
        # this answers.
        "these_are_a_share_of_their_year_not_a_headcount": (
            _VENTURE_SUPERVISION_NOTE if _is_venture else None),
        "more_supervision_than_you_have_free_right_now": (
            "the equivalent of %.2f scholars and %.2f artisans needed to "
            "keep it open (a share of their year, not a headcount); you "
            "have %.2f and %.2f free right now (not already watching "
            "something else). This is what 'open' will actually check, on "
            "the day you open it - hire, teach, or close something first."
            % (_sup_sch, _sup_art, _free_sch, _free_art)
            if _is_venture and (_sup_sch > _free_sch + 1e-9
                                or _sup_art > _free_art + 1e-9) else None),
    }


def _explain_staffing(s, nodes, k, node):
    """The build crew (staff_needed), what you have free right now, and -
    for a going concern - the separate, smaller-or-larger standing crew
    `open` actually checks.
    """
    # THE SUPERVISION FIGURE, from the SAME function open_venture() enforces
    # (see venture_hands, projects.py) - not a second estimate of it. Only
    # meaningful for something that could ever be a going concern; knowledge
    # alone (is_venture false) has nothing to keep an eye on.
    _is_venture = s.is_venture(k)
    _sup_sch, _sup_art = s.venture_hands(k) if _is_venture else (0.0, 0.0)
    _free_sch, _free_art = s.venture_staff_free() if _is_venture else (0.0, 0.0)
    _foreman_trade, _foreman_fte = (s.venture_foreman(k) if _is_venture
                                     else (None, 0.0))
    out = {}
    out.update(_staffing_build_crew(s, node))
    out.update(_staffing_standing_crew(s, _is_venture, _sup_sch, _sup_art, _free_sch,
                                        _free_art, _foreman_trade, _foreman_fte))
    return out


def _explain_classification(s, nodes, k, node):
    """Suspicion, state interest, bounty eligibility, and which of the
    three ways "finished, stays finished" applies to this node.
    """
    bounty_by_type = (node["cat"] in ("glass_optics", "metallurgy", "precision",
                      "power", "agriculture", "information", "instruments"))
    # is_venture is asked again here rather than threaded through from
    # _explain_staffing: it is a cheap, side-effect-free lookup (Sim.is_
    # venture reads only the node and s.household.granted), and asking it
    # again keeps this group's fields independent of that one's internals.
    _is_venture = s.is_venture(k)
    return {
        "suspicion": node.get("sus", 0), "state_interest_trait_score": node.get("gov", 0),
        "bounty_eligible_by_type": bounty_by_type,
        # NOT CHARGED UNTIL YOU OPEN IT: revenue and upkeep follow what you
        # RUN, so the figure quoted elsewhere is real but not yours yet
        # until you open it - this says so.
        "revenue_and_upkeep_apply_only_once_opened": (
            True if (node["rev"] > 0 or node["up"] > 0) and k not in s.granted
            and k not in s.operating else None),
        # "FINISHED, STAYS FINISHED" MEANS THREE DIFFERENT THINGS, and this
        # engine said it the same way for all three. Most of what you build is
        # a plain prerequisite: done once, it counts for ever, whatever you do
        # with it afterward (see missing_prerequisites below, which reads
        # `done`, never `running`). A CAPABILITY_INSTITUTIONS node is not that:
        # a school's scholars, a workshop's household places, a patron's
        # credit, and a patron's willingness to have his name behind
        # something the state is wary of, ALL stop the moment you close the
        # doors, exactly like its revenue and upkeep above - even though the
        # knowledge of how to run one never leaves you. identity_cover,
        # workshop_first and patron_local sit identically in `ventures`,
        # but closing them has very different consequences, so this says
        # which kind a node is, in the one place a player reads before
        # deciding.
        "this_is_a_capability_you_must_keep_open": (
            "yes - it is knowledge (that part is permanent), but scholars it "
            "supports, household places it adds, credit or standing it lends "
            "you, or a future start it clears all stop the moment you close "
            "it, the same as its revenue and upkeep. Closing it for the "
            "capital back gives up all of that, not only the money."
            if k in s.CAPABILITY_INSTITUTIONS else None),
        "permanent_on_completion": (
            "Knowledge and completion-based prerequisite credit remain even "
            "while this institution is closed." if _is_venture else
            "Knowledge and prerequisite credit remain permanently."),
        "only_while_open": (
            "Revenue, upkeep, supported staff, household places, credit, "
            "standing, capacity, and running-only prerequisites stop when it "
            "closes." if k in s.CAPABILITY_INSTITUTIONS else
            ("Revenue and upkeep apply only while open."
             if _is_venture else None)),
    }


def _lineage_setup(s, nodes, k):
    """The chain behind a node, what it unlocks, and how much rests on it -
    the four values every field in this group is built from. Returns
    (chain_all, need, unlocks, n_blocks).
    """
    # WHAT IS LEFT OF IT, not what it always was: the chain BEHIND a node
    # is a fixed fact about the tree, but what a player is deciding with
    # is what they still have to do, so `need` must subtract `s.done` -
    # otherwise the number never counts down no matter how much has
    # already been built.
    _chain_all = closure(nodes, k) - {k}
    need = _chain_all - s.done
    # req_any COUNTS AS UNLOCKING: a node can be reached two ways, as a
    # hard prerequisite in `pre`, or as one option inside a req_any
    # substitution group ("any of a steam engine, a water wheel or a
    # horse will drive this"). Scanning `pre` alone would report nodes
    # like the Norse clinker hull and bog-iron bloomery, or the Mexica's
    # chinampa, as dead ends - each civilisation's own signature
    # technology told it leads nowhere, when it genuinely unlocks
    # something through a substitution group.
    unlocks = [] if getattr(s, "fog", False) else _unlocked_by(k, nodes)
    # Was: {m for m in nodes if k in closure(nodes, m)} - a full ancestor
    # closure of all 2,831 nodes, per call. Same answers, computed once for the
    # whole tree and cached. See data.descendants.
    # THE CYCLE-SAFE WALK, not the cached bitmask. See the comment on the same
    # substitution in _node_explain's sibling below: the index follows hard
    # prerequisites only and cannot do otherwise, because req_any options make
    # the graph cyclic. This is the number a player reads as "nothing depends
    # on this", and `why sea_clinker_hull` was printing DIRECTLY UNLOCKS with a
    # node named on one line and TOTAL DOWNSTREAM: 0 on the next.
    n_blocks = len(_downstream_of(k, nodes))
    return _chain_all, need, unlocks, n_blocks


def _explain_visible_prerequisites(s, nodes, k, node):
    """Which prerequisites this node has, which are still missing, and how
    many more are hidden by fog than the visible lists let on.
    """
    return {
        # ONLY WHAT YOU HAVE HEARD OF. These are read for a visible node, where
        # every prerequisite is either done or itself heard of - except on the
        # goal, which `why` answers under fog because the status line names it
        # every turn. Unfiltered, that one exception printed the goal's seven
        # hidden prerequisites by name in the JSON, which is the fog exploit
        # this file has already closed twice.
        "direct_prerequisites": ([prereq_id for prereq_id in node["pre"] if s.is_visible(prereq_id)]
                                 if getattr(s, "fog", False) else node["pre"]),
        # A GRANTED NODE IS HELD, WHATEVER ROUTE THE TREE DRAWS TO IT. `why
        # cap_heat_1300` on Han reported done:true, missing_prerequisites:
        # ["cap_heat_1100"] and can_start_now:false in one object - three
        # statements that cannot all be true. The cause is not a broken graph
        # but a mis-read one: the tree encodes ONE acquisition route, and a
        # society that already has the thing did not travel it. The clearest
        # case is the Mexica, whose maize and chinampas hang off
        # exp_americas_factory - crossing the Atlantic and founding a trading
        # post - because that is how a European acquires maize. Closing the
        # prerequisites into the grant, the obvious-looking fix, would hand
        # Tenochtitlan sextants, pendulum clocks and cementation steel for
        # nothing. What is actually wrong is the claim that a thing you have
        # is missing something.
        "missing_prerequisites": ([] if k in s.granted
                                  else [prereq_id for prereq_id in node["pre"] if prereq_id not in s.done
                                        and (not getattr(s, "fog", False)
                                             or s.is_visible(prereq_id))]),
        "prerequisites_you_have_not_heard_of": (
            sum(1 for prereq_id in node["pre"] if not s.is_visible(prereq_id))
            if getattr(s, "fog", False) else 0) or None,
    }


def _explain_grant_route(s, nodes, k, node):
    """Whether this society already has the node without building it, and
    if so, that the prerequisite list above is somebody ELSE's route.
    """
    return {
        "held_without_building_it": k in s.granted,
        "prerequisites_are_how_another_society_would_get_this": (
            "this society already has it; the list above is the route somebody "
            "who did not would have to take" if k in s.granted and node["pre"]
            else None),
    }


def _explain_prerequisites(s, nodes, k, node):
    """Which prerequisites are missing, which are hidden by fog, and
    whether this society already has the node by a route other than
    building it.
    """
    out = {}
    out.update(_explain_visible_prerequisites(s, nodes, k, node))
    out.update(_explain_grant_route(s, nodes, k, node))
    return out


def _explain_chain(s, nodes, k, need, _chain_all):
    """The size, hours and cost of the chain still standing behind this
    node - fogged, since it is a map of the tree you have not seen.
    """
    return {
        # Same reasoning: the size and cost of everything BEHIND a node is a
        # measurement of a tree you cannot see. You do know how many of its own
        # prerequisites you are still missing, because those have names you have
        # either heard or not.
        "chain_size": (len(need) if not getattr(s, "fog", False) else None),
        "chain_size_counting_what_you_have_built": (
            len(_chain_all) if not getattr(s, "fog", False) else None),
        "chain_founder_hours": (sum(nodes[node_id]["ph"] for node_id in need)
                                if not getattr(s, "fog", False) else None),
        # AT THIS SOCIETY'S PRICES, like the COST line four rows above it:
        # summing the tree's BASE cost and applying none of the
        # civilisation-specific multipliers the same page prints would
        # disagree badly - the eight prerequisites of a telescope, say,
        # summing the same in every civilisation regardless of a real bill
        # that varies by civilisation. chain_size and chain_founder_hours
        # are unaffected by price; only chain_cost has to go through
        # s.project_cost().
        "chain_cost": (round(sum(s.project_cost(node_id) for node_id in sorted(need)), 1)
                       if not getattr(s, "fog", False) else None),
        "critical_path_years": (critical_path(nodes, k)[0]
                                if not getattr(s, "fog", False) else None),
    }


def _explain_unlocks(s, nodes, k, unlocks, n_blocks):
    """What this leads to, and how much rests on it - the forward-looking
    half of lineage, banded rather than counted under fog.
    """
    return {
        # DOWNSTREAM COUNT IS A SPOILER UNDER FOG: an exact count of
        # everything a thing leads to is a map of the tree a player was
        # told they could not see, letting a handful of large numbers give
        # away the hub nodes the whole early strategy turns on.
        #
        # What survives fog is the thing a person in the year 100 could actually
        # judge: whether this is a foundation others will build on, or an end in
        # itself. You can tell that much by looking at it.
        "unlocks": unlocks,
        "downstream_count": (n_blocks if not getattr(s, "fog", False) else None),
        "how_much_rests_on_this": (
            None if not getattr(s, "fog", False) else _rests_band(n_blocks)),
        # Under fog there is no visible goal, so a boolean saying whether
        # this is "on the goal path" would be either meaningless or a
        # leak, and must be None instead of true/false.
        "on_goal_path": (None if getattr(s, "fog", False)
                         else (k == s.goal or is_downstream(nodes, k, s.goal))),
    }


def _explain_lineage(s, nodes, k, node):
    """Where this sits in the tree: prerequisites missing and heard-of,
    the chain behind it, what it unlocks, and how much rests on it -
    fogged wherever the exact figure would be a map of the tree.
    """
    _chain_all, need, unlocks, n_blocks = _lineage_setup(s, nodes, k)
    out = {}
    out.update(_explain_prerequisites(s, nodes, k, node))
    out.update(_explain_chain(s, nodes, k, need, _chain_all))
    out.update(_explain_unlocks(s, nodes, k, unlocks, n_blocks))
    return out


def _explain_status(s, nodes, k, node):
    """Done, active, startable now, and why not."""
    started = k in s.done or k in s.active
    return {
        "done": k in s.done, "active": k in s.active,
        "can_start_now": (not started) and s.can_start(k),
        # FOG-SCRUBBED: naming a locked prerequisite in full here would leak
        # its name and description through an unrelated node's explanation,
        # even while `why` on that prerequisite itself says it has never
        # been heard of. If you cannot see a thing, you cannot see its name
        # in someone else's sentence either.
        "start_blocked_reason": None if started else s.fog_scrub(s.start_reason(k)[1]),
    }


def _explain_active_wait(s, nodes, k):
    """What is holding an active project up, for the one project a player
    named by id - empty for anything not currently active.
    """
    # WHAT IS ACTUALLY HOLDING AN ACTIVE PROJECT UP, on the one screen a
    # player names it by id to read. `state` already says this for every
    # RUNNING project (see _waiting_on's own comment: a project can only
    # absorb its cost divided by its calendar floor in any one year,
    # however much cash is in hand, and a Han player watched abundant
    # capital sit idle against cheap projects for years before inferring the
    # mechanism themselves). `why <id>` on that same project said nothing of
    # the kind - STATUS: ACTIVE and no more - which is exactly the screen a
    # player checking on one specific stalled project would reach for.
    out = {}
    if k in s.active:
        _st = s.active[k]
        _bill = _st.get("cost_left")
        if _bill is None:
            _bill = max(0.0, s.project_cost(k) - _st["spent"])
        out["waiting_on"] = _waiting_on(s, nodes, k, _st, _bill)
        # SAME FIELD `state` ALREADY PRINTS PER PROJECT, HERE TOO. Arrears
        # gives unspendable founder hours back (core.py's underfunded path),
        # so ph_left never sits at 0 and waiting_on's money branch above can
        # never fire - "waiting on: your hours" is what a player in arrears
        # sees here, full stop, on the one screen that names a single
        # project by id. why_underfunded is the real reason, already
        # computed onto this same st dict; only render_state read it before.
        out["why_underfunded"] = _st.get("why_underfunded")
    return out


def _explain_labour_notes(s, node):
    """Notes on the two labour fields, added only when this node makes
    them matter: a hired trade that does not exist here yet, one that
    exists but has nobody trained and ready, or a build crew bigger than
    what is already on staff.
    """
    out = {}
    # Say what the two labour fields mean ONLY when this node makes it
    # matter: without context the two fields can read as contradicting
    # each other, so the explanation earns its place; carrying it on
    # every reply whether or not the node hires anyone is 400 bytes of
    # boilerplate per call.
    absent = sorted(trade for trade in node["lab"] if not s.trade_available(trade))
    if absent:
        out["trades_that_do_not_exist_here"] = absent
        out["hired_labour_means"] = ("hours of a trade bought in for this job only. "
                                     "These trades do not exist here yet and must "
                                     "be taught; see the labour command.")
    # TRAIN AND HIRE ARE TWO STEPS, and a project asking for a taught trade
    # went quiet about it the moment `train` was called - trade_available()
    # (what `absent` above checks) goes true instantly, years before anyone
    # actually graduates or is hired in. `start` catches the real shortage
    # (market_supply, not trade_available) and refuses; `why` said nothing
    # about it beforehand. A Rome player hit that refusal with no warning on
    # either this screen or train's own success message.
    _taught_but_empty = sorted(trade for trade in node["lab"]
                               if trade not in absent and s.market_supply(trade) <= 0.0)
    if _taught_but_empty:
        out["trades_taught_but_nobody_here_to_do_them_yet"] = _taught_but_empty
        out["trades_taught_but_nobody_here_means"] = (
            "the trade exists here, but nobody is trained and ready: a "
            "project draws only on people actually held in a taught trade, "
            "never a general market for it. If someone is still learning "
            "this may still let the work start and then stall at 0 progress "
            "on this trade until they finish; if nobody is even learning it "
            "yet, starting is refused outright. Check 'labour' for who is "
            "in training, or 'hire' to add people to this trade right now.")
    if node["art"] > s.artisans or node["sch"] > s.effective_scholars():
        out["staff_needed_means"] = ("people kept on your own staff, who understand "
                                     "your methods and stay when this is finished. "
                                     "Different from hired_labour, which is hours of "
                                     "a job.")
    return out


def _node_explain(s, nodes, k):
    """The full report on one node: prerequisites, costs, hours, risks,
    what it unlocks, and why it cannot be started, if it cannot.

    Split into one function per concern, matching the sections `why` has
    always had (identity, cost, revenue, timing and risk, staffing,
    classification, lineage, status, and two trailing notes that only
    apply sometimes) - this function assembles their pieces in that same
    order, and decides nothing itself.
    """
    node = nodes[k]
    out = {}
    out.update(_explain_identity(s, nodes, k, node))
    out["cost"] = _explain_cost(s, nodes, k, node)
    out.update(_explain_revenue(s, nodes, k, node))
    out.update(_explain_timing_and_risk(s, nodes, k, node))
    out.update(_explain_staffing(s, nodes, k, node))
    out.update(_explain_classification(s, nodes, k, node))
    out.update(_explain_lineage(s, nodes, k, node))
    out.update(_explain_status(s, nodes, k, node))
    out.update(_explain_active_wait(s, nodes, k))
    out.update(_explain_labour_notes(s, node))
    return out
