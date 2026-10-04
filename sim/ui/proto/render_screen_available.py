"""The available screen: the per-technology row and the blocks render_available assembles."""

import textwrap
from .util import _fmt_num, _fmt_range, _pct, _wrap
from .tree_filters import render_state_rows, stock_line


_RESTS_SHORT = {"almost everything": "ALL", "a great deal": "much",
                "a fair amount": "some", "a few things": "few",
                "a little": "1-3",
                "nothing else; this is worth having for itself": "-"}


def _cost_marker(entry):
    """A row you cannot pay for today gets its cost marked.

    "MOST RESTS ON THESE" can head its list with items well beyond an
    opening purse. The advice is right - those really are the nodes
    everything rests on - and the reader still needs to know which of
    them they can act on this year.
    """
    return "*" if entry.get("cannot_pay_now") else ""


def _available_row(entry, width=None, purse=None):
    # THE FLOOR SCALES WITH DISPLAY_WIDTH, NOT A BARE 34. render_available
    # already grows this per-table to fit the longest id on the page (see
    # its own comment on _w below), so a narrow default never truncated one;
    # this only gives a wide terminal the same extra breathing room _wrap
    # gets, and reproduces exactly 34 at DISPLAY_WIDTH's own old default
    # (76), so nothing here moves for a player who has changed nothing.
    if width is None:
        # LIVE, NOT A SNAPSHOT: see _wrap's own comment on DISPLAY_WIDTH,
        # in sim/ui/proto/util.py, for why this goes through the protocol
        # module rather than the plain imported name.
        from sim.ui import protocol as _protocol
        width = max(34, _protocol.DISPLAY_WIDTH - 42)
    hours = entry.get("founder_hours", entry.get("your_hours"))
    years = entry.get("calendar_floor_years", entry.get("least_years"))
    risk = entry.get("risk", entry.get("chance_of_failure"))
    downstream_count = entry.get("downstream_count")
    rests = (_fmt_num(downstream_count) if downstream_count is not None
             else _RESTS_SHORT.get(entry.get("how_much_rests_on_this"), "?"))
    if entry.get("on_road_to_goal"):
        rests += ">"   # on the road to your goal; the legend says so
    # THE ID IS NOT DECORATION, IT IS THE NEXT THING YOU TYPE: truncating
    # it would mean the longest ids could not be copied out of the table
    # at all, and `start` would refuse an id the table had just printed
    # incomplete. Names get cut instead; nobody has to retype a name.
    staff = entry.get("needs_staff") or "-"
    if entry.get("short_of_staff"):
        staff += "*"
    foreman = entry.get("specialist_foreman")
    payback = entry.get("payback_years")
    name_lines = textwrap.wrap(entry.get("name") or "", _AVAILABLE_NAME_WIDTH,
                               break_long_words=True) or [""]
    row = _AVAILABLE_ROW_FORMAT % (
        width, (entry.get("id") or ""), name_lines[0],
        _fmt_num(entry.get("cost")) + _cost_marker(entry),
        _fmt_num(hours), _fmt_num(years), _pct(risk),
        _fmt_range(entry.get("earns_per_year")), _fmt_num(entry.get("costs_per_year_after")),
        _fmt_num(entry.get("net_per_year")) if "net_per_year" in entry else "-",
        _fmt_num(payback) if payback is not None else "-",
        staff, (foreman["trade"][:7] if foreman else "-"), rests)
    # The rest of a long name goes on the lines below, under the NAME column.
    stock = [" " * (width + 1) + stock_line(entry)] if entry.get("living_stock") else []
    return "\n".join([row] + [" " * (width + 1) + name_line
                             for name_line in name_lines[1:]] + stock)


_AVAILABLE_NAME_WIDTH = 14
_AVAILABLE_ROW_FORMAT = "%-*s %-14s %9s %5s %5s %5s %8s %7s %8s %5s %6s %-7s %6s"


def available_header(width):
    return _AVAILABLE_ROW_FORMAT % (
        width, "ID", "NAME", "COST", "HOURS", "YEARS", "RISK", "EARNS/YR", "UPKEEP",
        "NET/YR", "PAYB", "STAFF", "FOREMAN", "RESTS")


# render_available is split the same way: the header/width setup, then one
# function per mutually exclusive content branch (the subject digest, the
# empty-search message, the full list) - render_available itself keeps the
# original if/elif/elif choosing which one to call, so exactly one of them
# ever runs, exactly as before - then the legend and the trailing notes.

def _available_top(out):
    """The count/showing/sorted-by lines, the purse, and the column header
    string every branch below needs - computed once, here, rather than by
    each branch separately.
    """
    lines = ["AVAILABLE: %s startable now" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        lines.append(out["showing"])
    if out.get("sorted_by"):
        lines.append("sorted by: %s" % out["sorted_by"])
    lines.append("")
    # Sized to the longest id ON THIS PAGE, so the table stays aligned without
    # ever cutting the one string the player has to type next.
    _purse = out.get("you_could_raise_for_a_project")
    _rows_here = (out.get("available") or []) + (out.get("cheapest_now") or [])
    _width = max([34] + [len(row.get("id") or "") for row in _rows_here
                     if isinstance(row, dict)])
    header = available_header(_width)

    return lines, _purse, _width, header


def _available_subjects_block(out, header, _width, _purse):
    lines = []
    lines.append("%-24s %8s %10s %10s %10s" % ("SUBJECT", "THINGS", "CHEAPEST", "DEAREST", "AFFORD"))
    for summary_row in out["subjects"]:
        lines.append("%-24s %8s %10s %10s %10s" % (
            summary_row["subject"][:24], _fmt_num(summary_row["things"]), _fmt_num(summary_row["cheapest"]),
            _fmt_num(summary_row["dearest"]), _fmt_num(summary_row["you_could_pay_for"])))
    lines.append("")
    lines.append("CHEAPEST RIGHT NOW, sorted by cost:")
    lines.append(header)
    for entry in sorted(out.get("cheapest_six") or [], key=lambda e: e.get("cost", 0)):
        lines.append(_available_row(entry, _width, _purse))
    if out.get("most_rests_on_these"):
        lines.append("")
        lines.append("MOST RESTS ON THESE, of what you could begin today:")
        lines.append(header)
        for entry in out["most_rests_on_these"]:
            lines.append(_available_row(entry, _width, _purse))
    lines.append("")
    for label, value in (out.get("to_see_more") or {}).items():
        lines.append("  %s: %s" % (label, value))
    return lines


def _available_empty_block(out):
    lines = []
    # No column headings over no rows: a table with headers but no rows
    # underneath reads as ambiguous, unclear whether the search failed or
    # something is broken.
    lines.append(out.get("nothing_matched")
             or "Nothing you could begin today matches that.")
    if out.get("known_but_blocked_matches"):
        lines.append("%d known but not startable yet match: add state:blocked to list them."
                     % out["known_but_blocked_matches"])
    hint = out.get("try_instead") or {}
    if hint.get("tags"):
        lines.append("Topics with things you know of (use tag:<name>):")
        for entry in hint["tags"]:
            lines.append("  %-24s %d startable, %d blocked" % (
                entry["tag"], entry["startable"], entry["blocked"]))
    for entry in hint.get("closest_visible", []):
        lines.append("  close: %s (%s), %s" % (entry["name"], entry["id"], entry["state"]))
    return lines


def _available_list_block(out, header, _width, _purse):
    lines = []
    lines.append(header)
    # IN THE ORDER THE REPLY GAVE IT, not re-sorted by cost here. A player
    # who asked for {"sort":"risk"} got a JSON list in risk order and a
    # printed table back in cost order underneath it - the JSON and the
    # words describing the same reply disagreeing about what "sorted"
    # meant. _agent_available already sorts the page exactly the way it
    # was asked to; the one thing this renderer must not do is undo that.
    for entry in out["available"]:
        lines.append(_available_row(entry, _width, _purse))
    if out.get("more"):
        lines.append("")
        lines.append(out["more"])
    if out.get("how_matched"):
        lines.append("")
        lines.append("  Search: " + out["how_matched"] + ".")
    return lines


def _available_legend_block(out, _purse):
    lines = []
    # LEGEND, once, and only when a table was actually printed. "1a*" means
    # nothing to a reader who has not been told; the column exists to be read
    # at a glance and a glance does not include guessing.
    _shown = ((out.get("available") or []) + (out.get("cheapest_six") or [])
              + (out.get("most_rests_on_these") or []))
    if _shown:
        lines.append("")
        lines.append("  STAFF is the standing people it needs: 2s = two scholars, "
                 "1a = one craftsman.")
        if out.get("estimates_note"):
            lines.append(_wrap("  COST, HOURS, YEARS and STAFF are estimates (~). "
                               + out["estimates_note"], indent="  "))
        lines.append("  NET/YR is earnings less upkeep; PAYB is years to earn the cost back "
                 "(takings ramp up over the first years, upkeep does not); FOREMAN is "
                 "the specialist trade 'open' will need free.")
        if any(entry.get("short_of_staff") for entry in _shown if isinstance(entry, dict)):
            lines.append("  A * after STAFF means you do not have them yet - 'hire' "
                     "or 'train' first, or the work waits.")
        if any(entry.get("on_road_to_goal") for entry in _shown if isinstance(entry, dict)):
            lines.append("  A > after RESTS means your goal needs it; it says nothing of how far away it is.")
        if _purse is not None and any(_cost_marker(entry) for entry in _shown
                                      if isinstance(entry, dict)):
            lines.append("  A * after COST means `start` would refuse it today (`start <id>` "
                     "says why); between cash and credit you can put %s into a project."
                     % _fmt_num(_purse))
    return lines


def _available_trailing_block(out):
    lines = []
    heard = out.get("heard_of_but_cannot_begin")
    if heard:
        lines.append("")
        lines.append("HEARD OF, CANNOT BEGIN YET:")
        for heard_row in heard:
            lines.append("  %-34s %s" % (heard_row["id"], heard_row.get("why_not") or ""))
        if out.get("and_more_you_have_heard_of"):
            lines.append("  " + str(out["and_more_you_have_heard_of"]))
    if out.get("to_sort_or_page_differently"):
        lines.append("")
        lines.append(_wrap(out["to_sort_or_page_differently"]))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return lines


def render_available(out):
    """A scannable table: every column aligned, sorted cheapest-first so the
    same eye scan works whether you are looking for a bargain or a subject.
    """
    if "rows" in out and out.get("state"):
        return render_state_rows(out)
    lines, _purse, _width, header = _available_top(out)
    if "subjects" in out:
        lines += _available_subjects_block(out, header, _width, _purse)
    elif "available" in out and not out["available"]:
        lines += _available_empty_block(out)
    elif "available" in out:
        lines += _available_list_block(out, header, _width, _purse)

    lines += _available_legend_block(out, _purse)
    lines += _available_trailing_block(out)
    return "\n".join(lines)
