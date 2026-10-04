"""The event log reply: failure markers, filters, paging and _agent_log."""
from .notes_store import NoteLine, note_log_rows



# A LOG LINE A PLAYER WOULD CALL BAD NEWS: self.log already records every
# failure, in the founder's own words, with no field anywhere marking
# which lines are the bad ones. Matched on the actual wording every
# append site already uses (self.log.append across core.py, projects.py,
# economy.py and society.py), not reinvented here.
_FAILURE_MARKERS = (
    "FAILED", "HALTED", "ABANDONED", "CREDIT EXHAUSTED", "CLOSE TO THE LIMIT",
    "IN ARREARS", "in arrears", "INSOLVENCY", "BONDAGE", "cannot go on",
    "cannot pay everyone", "SHORT OF", "nobody left to keep an eye",
    "disperses", "sacked", "KNOWLEDGE LOST", "destroyed", "confiscated",
    "founder dies", "RUN ENDS", "MOTHBALLED",
)


def _is_failure_line(msg):
    # CASE-INSENSITIVELY, because these markers are prose and prose gets
    # rewritten. The founder's death line was recapitalised to say what the
    # death MEANS rather than only that it happened, and silently stopped
    # being a failure line here, in `log failures`, which is the one screen a
    # player checks to find out what went wrong.
    if isinstance(msg, NoteLine):
        return False
    _low = msg.lower()
    return any(marker.lower() in _low for marker in _FAILURE_MARKERS)


def _log_scrub(sim, text):
    """A log line, with anything the player cannot currently see redacted.

    self.log stores what happened IN THE YEAR IT HAPPENED, in plain English,
    and can go on naming a thing for centuries after fog would refuse to
    answer `why` about it - either because a sacking took it away (see
    knowledge_risk's `forgotten`) or, for a hazard's own advice, because it
    names a hedge the player never found. `fog_scrub` already strips ids out
    of a message; most of this engine's own log lines name the thing, not the
    id - "completed: Horizontal loom", not "completed: tex_horizontal_loom" -
    so this also strips NAMES of anything not currently visible.
    """
    if isinstance(text, NoteLine):
        return text
    text = sim.fog_scrub(text)
    if not sim.fog or not text:
        return text
    memo = {}
    for node_id, node in sim.nodes.items():
        node_name = node.get("name")
        if node_name and node_name in text and not sim.is_visible(node_id, _memo=memo):
            text = text.replace(
                node_name, "something you have since forgotten"
                    if node_id in (sim.forgotten or {}) else
                    "something you have not heard of")
    return text


def _agent_log_parse_filters(cmd):
    """The which-lines filters from the raw cmd dict: whether to keep
    only failure lines, a lowercase search term, and a since/before year
    range. Garbage input is tolerated the same way the inline parsing
    inside _agent_log always did - a bad since/before falls back to None.
    """
    only_fail = bool(cmd.get("failures")
                     or str(cmd.get("only") or "").strip().lower() in
                        ("failures", "failure", "fails", "fail"))
    find = str(cmd.get("find") or cmd.get("search") or "").strip().strip('"\'').lower()
    try:
        since = int(cmd["since"]) if str(cmd.get("since", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        since = None
    try:
        before = int(cmd["before"]) if str(cmd.get("before", "")).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        before = None
    return only_fail, find, since, before


def _agent_log_parse_paging(cmd):
    """Sort order, page size and offset from the raw cmd dict, with the
    hard cap on `limit` that keeps a single reply from ever dumping the
    whole log.
    """
    order = str(cmd.get("order") or "newest").strip().lower()
    if order not in ("newest", "oldest"):
        order = "newest"
    try:
        limit = int(cmd.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    # THE HARD CAP THAT MAKES "NEVER DUMPED IN ONE GO" TRUE REGARDLESS OF WHAT
    # IS ASKED FOR. Every other paged screen in this game trusts `limit` to
    # whatever a script asks; this one cannot, because the failure mode this
    # command exists to prevent - a reply so large it overflows a reader's
    # context - is exactly what a script asking for {"limit":100000} would
    # otherwise get.
    limit = max(1, min(limit, 100))
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    return order, limit, offset


def _agent_log_filter_rows(log, since, before, only_fail):
    """The since/before year range and the failures-only filter, applied
    in that order to every (index, (year, msg)) row of the log.
    """
    rows = list(enumerate(log))
    if since is not None:
        rows = [row for row in rows if row[1][0] >= since]
    if before is not None:
        rows = [row for row in rows if row[1][0] <= before]
    if only_fail:
        rows = [row for row in rows if _is_failure_line(row[1][1])]
    return rows


def _agent_log_search_rows(sim, rows, find, order):
    """The free-text search filter, confirmed against what fog actually
    lets the player see. Split from _agent_log_filter_rows because this
    filter alone needs the fog recheck below it - see its own comment.
    """
    if find:
        # CHEAP FIRST, then confirmed against what fog actually lets the
        # player see. A search that only matched a name fog is about to
        # redact would otherwise report "3 lines mention X" as proof
        # something called X exists, which is the same leak the visibility
        # guard on `why` exists to close, reached from a different command.
        rows = [row for row in rows if find in row[1][1].lower()]
        if sim.fog:
            # THE RECHECK IS THE EXPENSIVE HALF, one node sweep per candidate
            # line, so a common word over a run's whole history could be
            # thousands of sweeps. Capped to the most recent slice, which is
            # also the one this command defaults to showing: a search that
            # matches more than this has to narrow the word, the same as a
            # search with no fog concern at all would still have to page.
            _cap = rows[-2000:] if order != "oldest" else rows[:2000]
            rows = [row for row in _cap if find in _log_scrub(sim, row[1][1]).lower()]
    return rows


def _agent_log_page(sim, rows, order, offset, limit):
    """Order, then slice out the requested page, then scrub each
    surviving line for fog. Returns the total row count (before paging)
    and the page's own entries.
    """
    total = len(rows)
    ordered = list(reversed(rows)) if order == "newest" else rows
    page = ordered[offset:offset + limit]
    entries = [{"year": year, "what": _log_scrub(sim, msg)} for _idx, (year, msg) in page]
    return total, entries


def _agent_log_reply(log, total, offset, entries, find, only_fail, since, before, order):
    """Assemble the JSON reply around one page of entries: the count,
    the human-readable "showing" line, "more" when there is another
    page, and a note when the log or the filtered result is empty.

    len(entries) stands in for the original len(page): _agent_log_page
    builds entries one-for-one from page, never dropping a row, so the
    two lengths are always equal.
    """
    out = {"ok": True, "count": total,
           "showing": ("nothing" if not entries else
                      "%d-%d of %d, %s first"
                      % (offset + 1, offset + len(entries), total, order)),
           "entries": entries}
    if offset + len(entries) < total:
        out["more"] = ('%d more; ask again with "offset": %d'
                       % (total - offset - len(entries), offset + len(entries)))
    if not log:
        out["note"] = "nothing has happened yet"
    elif not entries and (find or only_fail or since is not None or before is not None):
        out["note"] = "nothing in your history matches that."
    # DISCOVERABLE ON THE SCREEN ITSELF, not only in `help`. A naive player
    # is not going to guess that this command takes filters at all.
    out["to_filter_or_sort"] = (
        "add 'failures':true for only what went wrong, 'find' to search, "
        "'since'/'before' for a year range, 'order':'oldest' to read forward "
        "from the start instead of back from now, and 'offset' to page "
        "through to the end.")
    return out


def _agent_log(sim, cmd=None):
    """The player's own history: what they did, and what followed from it.

    The commonest complaint across eleven rounds of playtesting was some
    version of "failures are silent" - a project stalling, a concern closing
    for want of staff, a hazard landing - none of it visible anywhere once
    the turn it happened had scrolled past. The engine has always kept every
    one of these in self.log; there was simply no command to read it back.

    NEVER THE WHOLE THING. A run of any length runs to tens of thousands of
    lines, more than an agent's whole context window, so this always pages
    and defaults to a recent window - `limit` is hard-capped, not merely
    suggested, and there is no `all:true` here the way `available` has one.
    """
    cmd = cmd or {}
    log = sorted(list(sim.log or []) + note_log_rows(sim), key=lambda row: row[0])  # notes join their year
    only_fail, find, since, before = _agent_log_parse_filters(cmd)
    order, limit, offset = _agent_log_parse_paging(cmd)
    rows = _agent_log_filter_rows(log, since, before, only_fail)
    rows = _agent_log_search_rows(sim, rows, find, order)
    total, entries = _agent_log_page(sim, rows, order, offset, limit)
    return _agent_log_reply(log, total, offset, entries, find, only_fail, since, before, order)
