"""Per-project rows of the `portfolio` screen (Complaints/88): what was allocated vs what is forecast."""

from .util import _fmt_num, _wrap


def project_lines(row):
    """One project: the last resolved allocation, then the forecast from now."""
    directed = row.get("hours_directed_this_year")
    rank, count = row.get("pool_rank_this_year"), row.get("pool_active_count_this_year")
    lines = ["", "  %-28s [%s]%s" % (row["name"], row["constraint"].replace("_", " "),
                                     "  (allocate: %s hrs/yr)" % _fmt_num(directed) if directed else "")]
    lines.append("    last allocation (set when the year last resolved): %s offered, %s effective%s"
                 % (_fmt_num(row.get("hours_offered_this_year")), _fmt_num(row.get("hours_effective_this_year")),
                    "  (priority #%s of %s active)" % (rank, count) if rank and count else ""))
    if row.get("hours_effective_last_year") is not None:
        lines.append("    the year before that: %s effective" % _fmt_num(row["hours_effective_last_year"]))
    finish = row.get("earliest_completion_year")
    lines.append("    forecast from now: %s founder-hours to go, %s still to pay, draws %s/yr, earliest finish %s"
                 % (_fmt_num(row.get("founder_hours_left")), _fmt_num(row.get("remaining_investment")),
                    _fmt_num(row.get("annual_absorption")),
                    "year %s" % finish if finish is not None else "never at the last allocation"))
    lines.append(_wrap("waiting on: " + str(row.get("waiting_on")), indent="      "))
    if row.get("why_underfunded"):
        lines.append(_wrap(row["why_underfunded"], indent="      "))
    return lines


def paging_line(paging):
    """The 'and M more' pointer, or nothing when every row is shown."""
    if not paging or not paging.get("more"):
        return None
    return ("  ... and %d more%s: '%s' or '%s'"
            % (paging["more"], " in %s" % paging["group"] if paging.get("group") else "",
               paging["all_command"], paging["next_command"]))
