"""The situational and meta screens split out of render.py: render_values,
render_final, render_score, render_error, render_stuck, render_risk (and its
own helper _advice_line), render_generic (the fallback for every reply with
no renderer of its own), render_log, render_policy, render_rush and
render_path - screens that tell you where you stand, what happened, or what
is wrong, rather than reporting a ledger table. Pure presentation, same as
every module in this split: nothing here touches the live Sim - see render.py
and ARCHITECTURE.md.

render_path borrows _available_row from render_screens_big.py for its own
table of startable-today nodes, the one place here that reaches into the
"big" group.
"""

from .score import _score_lines
from .util import _factor, _fmt_num, _pct, _wrap
from .render_screens_big import _available_row

def render_values(out):
    lines = ["WHAT THIS SOCIETY BELIEVES"]
    for row in out.get("values") or []:
        lines.append("  %-22s %7s  %s" % (row["field"], _factor(row["value"]),
                                      row.get("means") or ""))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return "\n".join(lines)


def render_final(out):
    lines = ["=" * 70, "THE RUN IS OVER", "=" * 70]
    lines.append(_wrap(str(out.get("why") or ""), indent="  "))
    lines.append("")
    lines.append("  ended in %s AD" % _fmt_num(out.get("ended_in")))
    lines.append("  you built %s things; this society already had %s"
             % (_fmt_num(out.get("you_built")),
                _fmt_num(out.get("this_society_already_had"))))
    lines.append("  %s in hand, %s people, reputation %s, %s concerns running"
             % (_fmt_num(out.get("money")), _fmt_num(out.get("people")),
                _fmt_num(out.get("reputation")),
                _fmt_num(out.get("concerns_you_were_running"))))
    if out.get("failed_attempts"):
        lines.append("  %s attempts failed and had to be begun again"
                 % _fmt_num(out["failed_attempts"]))
    if out.get("the_goal"):
        lines.append("")
        _had = next((value for field, value in out.items() if field.startswith("you_had_")), 0)
        lines.append("  THE ROAD TO %s" % str(out["the_goal"]).upper())
        lines.append("    %s nodes in all; you had %s of them and %s were still to build"
                 % (_fmt_num(out.get("the_whole_road_was")), _fmt_num(_had),
                    _fmt_num(out.get("still_to_build_when_it_ended"))))
        nxt = out.get("the_next_things_would_have_been") or []
        if nxt:
            lines.append("    the next steps would have been: " + ", ".join(nxt))
    big = out.get("the_largest_things_you_built") or []
    if big:
        lines.append("")
        lines.append("  the largest things you built: " + ", ".join(big))
    if out.get("score") is not None:
        lines.append("")
        lines.append("  SCORE")
        lines.extend(_score_lines(out["score"], indent="    "))
    lines.append("=" * 70)
    return "\n".join(lines)


def render_score(out):
    lines = ["=" * 70, "SCORE", "=" * 70, ""]
    lines.extend(_score_lines(out))
    lines.append("=" * 70)
    return "\n".join(lines)


def render_error(resp):
    return "REFUSED: %s" % resp.get("error", "unknown error")


def render_stuck(out):
    lines = ["WHY YOU ARE NOT GETTING ON"]
    lines.append("  %s things you could begin, %s of them you could pay for"
             % (_fmt_num(out.get("you_could_begin")),
                _fmt_num(out.get("and_could_pay_for"))))
    if out.get("and_the_cheapest_thing_you_could_start_now"):
        lines.append("  cheapest of them: %s"
                 % out["and_the_cheapest_thing_you_could_start_now"])
    reasons = out.get("what_is_holding_you_up")
    lines.append("")
    if isinstance(reasons, str):
        lines.append("  " + reasons)
    else:
        for reason in reasons:
            lines.append("  %s:" % str(reason.get("what", "")).upper())
            if reason.get("why"):
                lines.append(_wrap(reason["why"], indent="    "))
            _why_underfunded = reason.get("each_why_underfunded") or {}
            for node_id, value in sorted((reason.get("each_waiting_on") or {}).items()):
                lines.append(_wrap("%s - waiting on %s" % (node_id, value), indent="    "))
                if _why_underfunded.get(node_id):
                    lines.append(_wrap(_why_underfunded[node_id], indent="      "))
            if reason.get("the_nearest_few"):
                lines.append(_wrap("nearest first: " + ", ".join(reason["the_nearest_few"]),
                               indent="    "))
    hole = out.get("and_you_are_in_a_hole")
    if hole:
        lines.append("")
        lines.append("  " + str(hole.get("you_are_stuck", "")).upper())
        for suggestion in hole.get("what_would_change_it") or []:
            lines.append(_wrap("- " + suggestion, indent="    "))
    if out.get("this_does_not_know_your_goal"):
        lines.append("")
        lines.append(_wrap(out["this_does_not_know_your_goal"], indent="  "))
    return "\n".join(lines)


def render_risk(out):
    knowledge_risk = out.get("knowledge_risk") or out
    year = out.get("year")
    lines = ["KNOWLEDGE AT RISK"]
    lines.append("technologies at risk: %s     chance lost if a site is sacked: %s     fraction lost when it happens: %s"
             % (_fmt_num(knowledge_risk.get("technologies_at_risk")), _pct(knowledge_risk.get("loss_chance_if_a_site_is_sacked")),
                _pct(knowledge_risk.get("fraction_lost_when_it_happens"))))
    lines.append("hedge: %s" % (knowledge_risk.get("hedged_by") or "none yet"))
    if knowledge_risk.get("you_have_already_lost"):
        lines.append("")
        lines.append("ALREADY LOST TO A SACKING: %s technolog%s, most recently in %s"
                 % (_fmt_num(knowledge_risk["you_have_already_lost"]),
                    "y" if knowledge_risk["you_have_already_lost"] == 1 else "ies",
                    _fmt_num(knowledge_risk.get("the_most_recent_went_in"))))
        lines.append(_wrap("you have to build these again: "
                       + ", ".join(knowledge_risk.get("and_have_to_build_again") or []),
                       indent="  "))
    if knowledge_risk.get("note"):
        lines.append(_wrap(knowledge_risk["note"]))
    lines.append("")
    for hazard in knowledge_risk.get("known_hazards_ahead") or []:
        yrs = hazard.get("years") or [0, 0]
        tag = "IN PROGRESS" if hazard.get("in_progress") else "%s-%s" % (yrs[0], yrs[-1])
        lines.append("[%s] %s" % (tag, hazard.get("name")))
        # REPEATED ROLLS, NOT ONE. A per-year percentage over a window that
        # can run decades reads as one low-stakes check, and it is not one:
        # the engine rolls it independently EVERY year the window is open
        # (SocietyMixin._shocks runs once per simulated year, and this same
        # hazard is tested again each time). A Rome player, shown a figure
        # like this and told nothing about the window, built the hedges the
        # game suggested, was sacked twice in the same window anyway, and
        # lost about 300,000 denarii and 17 in-progress projects. Say what
        # the window actually adds up to, not only the one year's die.
        _p_year = hazard.get("sack_chance_per_year")
        if _p_year:
            _y0, _y1 = yrs[0], yrs[-1]
            _from = max(_y0, year) if year is not None else _y0
            _span = max(1, int(round(_y1 - _from)) + 1)
            _p_eff = hazard.get("sack_chance_after_what_you_have_built")
            _p_use = _p_eff if _p_eff is not None else _p_year
            _cum = 1.0 - (1.0 - max(0.0, min(1.0, _p_use))) ** _span
            lines.append("  %s a year, checked EVERY year of this %d-year window "
                     "- not once: about %s chance at least one sacking lands "
                     "somewhere in it before the window closes"
                     % (_pct(_p_year), _span, _pct(_cum)))
        if hazard.get("note"):
            lines.append(_wrap(hazard["note"], indent="  "))
        for kind, advice in (hazard.get("what_you_can_do") or {}).items():
            lines.append(_advice_line(kind, advice))
        for kind in ("sack_chance", "staff_loss"):
            after = hazard.get("%s_after_what_you_have_built" % kind)
            if after is not None:
                lines.append("  %s after what you have built: %s" % (kind.replace("_", " "), _pct(after)))
        if hazard.get("staff_loss") is not None:
            lines.append("  staff loss is a separate %s chance EVERY year, not a "
                     "total for the epidemic: %d checks remain; that is about "
                     "%s chance of at least one wave and %s expected cumulative "
                     "staff loss at your current protection"
                     % (_pct(hazard.get("staff_loss_wave_chance_per_year", 0.32)),
                        hazard.get("remaining_annual_wave_checks", 1),
                        _pct(hazard.get("chance_of_at_least_one_staff_loss_wave", 0)),
                        _pct(hazard.get("expected_cumulative_staff_loss", 0))))
    return "\n".join(lines)


def _advice_line(kind, advice, indent="  "):
    """One hazard's exposure, in a sentence rather than a bare dict repr -
    playing this through a real run, {'you_currently_take': 1.0, 'because_of':
    [], 'what_would_help': '...'} printed as literal Python was the single
    worst line in the whole rendering.
    """
    if not isinstance(advice, dict):
        return "%s%s: %s" % (indent, kind.replace("_", " "), advice)
    take = advice.get("you_currently_take")
    because = advice.get("because_of") or []
    line = "%s%s: you take %s of it" % (indent, kind.replace("_", " "), _pct(take))
    if because:
        line += " (softened by %s)" % ", ".join(because)
    help_ = advice.get("what_would_help")
    if help_:
        line += "\n%s  what would help: %s" % (indent, help_)
    # AND WHICH OF THE THINGS IN FRONT OF YOU IS ONE OF THOSE: naming a
    # hedge only by category ("walls, firearms, powerful friends") is
    # useless against a startable list hundreds of items long. Naming the
    # ones a player can already see costs nothing and is the difference
    # between advice and a slogan.
    steps = advice.get("you_could_begin_now_toward_it") or []
    now = [step for step in steps if step.get("can_begin_now")]
    later = [step for step in steps if not step.get("can_begin_now")]
    if now:
        line += "\n%s  you could begin now: %s" % (
            indent, ", ".join("%s (%s, %s)"
                              % (step["id"], _fmt_num(step["cost"]),
                                 step.get("because_it_gives_you") or "a hedge")
                              for step in now))
    for step in later[:2]:
        line += "\n%s  %s is one of them, waiting on: %s" % (
            indent, step["id"], (step.get("waiting_on") or "").split(". To get")[0])
    return line


def render_generic(resp, indent=""):
    """Every other reply: a plain key: value dump, numbers made readable.

    Nothing here needs a bespoke renderer to be worth reading - hire, buy,
    quote and the rest are already a handful of fields - so this is the
    fallback for all of them rather than one function apiece.
    """
    lines = []
    for field, value in resp.items():
        if field == "ok":
            continue
        label = field.replace("_", " ")
        if isinstance(value, dict):
            if value:
                lines.append("%s%s:" % (indent, label))
                lines.append(render_generic(value, indent + "  "))
            else:
                lines.append("%s%s: (none)" % (indent, label))
        elif isinstance(value, list):
            if not value:
                lines.append("%s%s: (none)" % (indent, label))
            elif all(isinstance(item, (str, int, float)) and not isinstance(item, bool) for item in value):
                lines.append("%s%s: %s" % (indent, label, ", ".join(_fmt_num(item) if isinstance(item, (int, float)) else str(item) for item in value)))
            else:
                lines.append("%s%s:" % (indent, label))
                for item in value:
                    if isinstance(item, dict):
                        lines.append(indent + "  - " + ", ".join("%s=%s" % (key, value) for key, value in item.items()))
                    else:
                        lines.append("%s  - %s" % (indent, item))
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            lines.append("%s%s: %s" % (indent, label, _fmt_num(value)))
        else:
            lines.append("%s%s: %s" % (indent, label, value))
    return "\n".join(lines)


def render_log(out):
    """Your own history, a year and a line at a time, newest first by default.

    Plain lines rather than a table: these are sentences, of wildly varying
    length - "FAILED at X" runs to three clauses, "hired 2 smiths" is four
    words - and forcing them into columns would either truncate the long ones
    or waste most of a line of blank padding on the short ones.
    """
    lines = ["HISTORY: %s" % _fmt_num(out.get("count"))]
    if out.get("showing"):
        lines.append(out["showing"])
    lines.append("")
    if out.get("note") and not out.get("entries"):
        lines.append(out["note"])
    for entry in out.get("entries") or []:
        lines.append("  %4s AD  %s" % (entry.get("year"), entry.get("what")))
    if out.get("more"):
        lines.append("")
        lines.append(out["more"])
    if out.get("to_filter_or_sort"):
        lines.append("")
        lines.append(_wrap(out["to_filter_or_sort"]))
    return "\n".join(lines)


def render_policy(out):
    """The switches, under a plain statement of what they are.

    The warning below has to appear BEFORE the list of switches and their
    descriptions, wrapped rather than run together as one long line: the
    whole point of that paragraph is that it is read BEFORE somebody turns
    a switch on, not buried after eleven descriptions where a reader
    scanning for a switch name would never reach it.
    """
    # LIVE, NOT A SNAPSHOT: see _wrap's own comment on DISPLAY_WIDTH, in
    # engine/proto/util.py, for why this goes through the protocol module
    # rather than the plain imported name.
    from .. import protocol as _protocol
    DISPLAY_WIDTH = _protocol.DISPLAY_WIDTH
    lines = ["AUTOMATIC BEHAVIOUR"]
    if out.get("these_are_approximations_not_optimal_play"):
        lines.append(_wrap(out["these_are_approximations_not_optimal_play"],
                       indent="  "))
        lines.append("")
    # GROUPED BY WHETHER THEY ARE ACTUALLY RUNNING, not listed alphabetically
    # with the state as a word at the end of a name: every description here
    # is written in the present indicative, so a reader scanning
    # descriptions reads what looks like eleven statements of what the game
    # is doing right now, and would have to carry a separate column in
    # their head to know which are hypothetical. Two headings cost nothing
    # and remove the ambiguity: what is running, and what is not.
    pol = out.get("policy") or {}
    does = out.get("what_each_does") or {}
    switches_on = [switch for switch in sorted(pol) if pol[switch]]
    off = [switch for switch in sorted(pol) if not pol[switch]]
    for head, keys, empty in (
            ("RUNNING NOW:", switches_on, "  nothing is automatic just now: every one "
                                 "of these is off, and the game does only "
                                 "what you tell it to."),
            ("NOT RUNNING - these describe what each WOULD do if you turned "
             "it on:", off, None)):
        if not keys:
            if empty:
                lines.append("")
                lines.append(_wrap(empty))
            continue
        lines.append("")
        lines.append("  " + head if len(head) < 40 else _wrap("  " + head))
        for switch in keys:
            lines.append("  %-18s %s" % (switch, "ON" if pol[switch] else "off"))
            if does.get(switch):
                lines.append(_wrap(does[switch], width=DISPLAY_WIDTH - 8,
                               indent="        "))
    if out.get("changed"):
        lines.append("")
        lines.append("  changed: %s" % out["changed"])
    stopped = out.get("stopped_by") or out.get("but")
    if stopped:
        lines.append("")
        lines.append("  NOT ACTING JUST NOW:")
        if isinstance(stopped, dict):
            for switch, value in sorted(stopped.items()):
                lines.append(_wrap("%s - %s" % (switch, value), indent="    "))
        else:
            lines.append(_wrap(str(stopped), indent="    "))
    return "\n".join(lines)


def render_rush(out):
    lines = ["RUSH: %d started, %d not" % (out.get("count_started", 0),
                                       out.get("count_not_started", 0))]
    for row in out.get("started") or []:
        lines.append("  STARTED %s (%s): %s" % (row.get("id"), _fmt_num(row.get("cost")),
                                            row.get("name")))
    for row in out.get("not_started") or []:
        lines.append("  NOT STARTED %s: %s" % (row.get("id"), row.get("why")))
    if out.get("this_is_an_approximation_not_optimal_play"):
        lines.append("")
        lines.append(_wrap(out["this_is_an_approximation_not_optimal_play"]))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return "\n".join(lines)


def render_path(out):
    """The route to one goal, and - the join nobody had - which of the
    nodes still standing between here and there you could actually begin
    today, rather than leaving a player to reconstruct that join by hand
    or with a script outside the game.
    """
    lines = ["ROUTE TO %s  [%s]" % (out.get("name"), out.get("id"))]
    if out.get("done"):
        lines.append("You have already built this.")
        return "\n".join(lines)
    lines.append("%s node(s) still stand between here and there; %s of them you "
             "could start TODAY, %s are still waiting on something else"
             % (_fmt_num(out.get("remaining_count")),
                _fmt_num(out.get("startable_today_count")),
                _fmt_num(out.get("still_waiting_on_something_else"))))
    lines.append("")
    rows = out.get("startable_today_toward_this")
    lines.append("STARTABLE TODAY, TOWARD THIS GOAL  (cheapest first)")
    if isinstance(rows, list) and rows:
        _width = max([34] + [len(entry.get("id") or "") for entry in rows])
        lines.append("%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s"
                 % (_width, "ID", "NAME", "COST", "HOURS", "YEARS", "RISK", "EARNS/YR",
                    "UPKEEP", "STAFF", "RESTS"))
        for entry in rows:
            lines.append(_available_row(entry, _width, None))
        if out.get("and_more_startable_today"):
            lines.append("...and %s more" % _fmt_num(out["and_more_startable_today"]))
    else:
        lines.append("  nothing - " + (out.get("note") or
                 "everything left on this route is waiting on something else"))
    if out.get("on_this_route_but_shut_down"):
        lines.append("")
        lines.append("ON THIS ROUTE BUT SHUT DOWN: "
                 + ", ".join(out["on_this_route_but_shut_down"]))
        if out.get("reopen_them_with"):
            lines.append(_wrap("  " + out["reopen_them_with"]))
    if out.get("this_route_pays_for_nothing"):
        lines.append("")
        lines.append(_wrap("!! " + out["this_route_pays_for_nothing"]))
    if out.get("these_together_cost_more_than_you_can_raise"):
        lines.append(_wrap("!! " + out["these_together_cost_more_than_you_can_raise"]))
    return "\n".join(lines)
