"""The blocks of the state screen: header, money, founder, running, concerns, employment, standing and at-risk sections."""

from sim.ui import units_text
from .util import _coin_hoard_line, _fmt_num, _pct, _wrap
from sim.engine.ui_port import condition_line
from sim.engine.ui_port import warning_lines
from .state_shut_staffing import render_shut_for_want_of_staff


def _state_header(out):
    lines = []
    year = out.get("year")
    lines.append("=" * 60)
    # WITH THE CLOCK ON IT: the horizon must not sit only in a help topic
    # and never in a reply read every turn, or a player discovers it only
    # by overshooting it.
    left = out.get("years_left")
    lines.append(("YEAR %s%s" % (year, ("   (%s years to the horizon at %s)"
                                    % (_fmt_num(left), out.get("horizon_year")))
                             if left is not None else ""))
             if year is not None else "STATE")
    lines.append("=" * 60)
    if out.get("ended"):
        lines.append("")
        lines.append("*** THE RUN HAS ENDED: %s ***" % out.get("end_reason"))
    return lines


def _state_money(out):
    lines = []
    lines.append("")
    net_after = out.get("net_after_project_spend")
    net_plain = out.get("net_per_year")
    spend = out.get("project_spend_this_year")
    lines.append("Money: %s den" % _fmt_num(out.get("capital")))
    lines += _coin_hoard_line(out)
    # BOTH NUMBERS, ALWAYS - NOT ONE HIDING THE OTHER: net_after_project_spend
    # alone is capital in less what you owe, less whatever went into
    # projects THIS YEAR, so starting one expensive thing makes the
    # household look about to go broke on the very turn it is investing
    # soundly, indistinguishable from actually failing without a second
    # command (`money`) the tutorial never points at. The recurring figure
    # - what standing income clears with nothing new started - is the
    # honest one to watch, and it prints on the same line `state` is read
    # from every turn, not one command away.
    if net_plain is not None and net_after is not None:
        lines.append("  net %s%s den/yr, recurring - this is the one to watch"
                 % ("+" if net_plain >= 0 else "", _fmt_num(net_plain)))
        if abs(spend or 0) > 0.5 or round(net_after, 1) != round(net_plain, 1):
            lines.append("  this year also put %s den into projects, leaving "
                     "%s%s den/yr after that (one-off, not a sign the "
                     "recurring figure above has changed)"
                     % (_fmt_num(spend or 0),
                        "+" if net_after >= 0 else "", _fmt_num(net_after)))
    elif net_after is not None:
        lines.append("  net %s%s den/yr (after %s den into projects this year)"
                 % ("+" if net_after >= 0 else "", _fmt_num(net_after), _fmt_num(spend or 0)))
    elif net_plain is not None:
        lines.append("  standing net %s%s den/yr (does not count project spend)"
                 % ("+" if net_plain >= 0 else "", _fmt_num(net_plain)))
    if (out.get("capital") or 0) < 0 and out.get("sustainable_debt") is not None:
        lines.append("  you owe %s; sustainable debt at your recurring surplus is %s "
                     "(`money` explains)"
                     % (_fmt_num(-out["capital"]), _fmt_num(out["sustainable_debt"])))
    if out.get("in_bondage_for_debt"):
        lines.append("IN DEBT BONDAGE: %s years left owing %s den"
                 % (_fmt_num(out["in_bondage_for_debt"]), _fmt_num(out.get("debt_still_to_work_off"))))
    return lines


def _staffing_warning_sentences(warnings):
    """One sentence per warning, except that concerns sharing the same
    household-wide spare headcount are named together in a single line."""
    sentences = []
    shared = {}
    for warning in warnings or []:
        if not isinstance(warning, dict):
            sentences.append(warning)
        elif (not warning.get("one_loss_closes_it")
              and (warning.get("headline") or "").endswith("before it closes")):
            shared.setdefault((warning.get("within"), warning.get("of")), []).append(warning)
        else:
            sentences.append(warning.get("headline"))
    for (within, word), group in shared.items():
        if len(group) == 1:
            sentences.append(group[0]["headline"])
            continue
        names = [warning.get("name") for warning in group]
        sentences.append("%s and %s: the household has %s spare %s before these close"
                         % (", ".join(names[:-1]), names[-1],
                            ("%.1f" % within).rstrip("0").rstrip("."), word))
    explained = {}
    for warning in warnings or []:
        if isinstance(warning, dict) and warning.get("explained"):
            explained.setdefault(warning.get("of"), warning["explained"])
    sentences.extend(explained.values())
    return sentences


def _founder_age_words(out):
    if not out.get("founder_ages"):
        return " (you do not age)"
    if not out.get("founder_alive"):
        return ""
    age, usual = out.get("founder_age"), out.get("founder_usual_age_at_death")
    if age is None:
        return ""
    words = ", aged about %s" % age
    if usual:
        words += " (people in your place mostly die between %s and %s%s)" % (
            usual[0], usual[1], "; you are past the middle of that" if age >= (usual[0] + usual[1]) / 2 else "")
    return words


def _state_founder(out):
    lines = []
    # WHETHER YOU AGE IS A FACT ABOUT THE GAME YOU ARE PLAYING, and the human
    # rendering did not carry it: a mortal run and an immortal one looked
    # identical here, though the menu asks you to choose between them and one
    # of them ends with everything you have not made permanent dying with you.
    _src = out.get("where_your_hours_come_from") or {}
    _dep = _src.get("deputies_who_direct_work_for_you") or 0
    # THE AGE, ON THE LINE THAT ALREADY SAYS DEAD OR ALIVE, not only inside
    # a log sentence from however many years ago: leaving it only in
    # `events` means it can scroll out of view long before a player thinks
    # to look for it.
    lines.append("You: %s%s, %s founder-hours free this year%s"
             % ("alive" if out.get("founder_alive") else
                ("DEAD (aged about %s at death, in %s)"
                 % (out.get("founder_died_aged"), out.get("founder_died_in"))
                 if out.get("founder_died_aged") is not None else "DEAD"),
                _founder_age_words(out),
                _fmt_num(out.get("founder_hours_available")),
                ("   (%s of your own, plus %s deputies directing work in your "
                 "name at %s hours each)"
                 % (_fmt_num(_src.get("you")), _fmt_num(_dep),
                    _fmt_num(_src.get("hours_each_deputy_adds"))))
                if _dep else ""))
    for _warning in _staffing_warning_sentences(out.get("supervision_close_to_the_edge")):
        # Each entry is a dict (see staffing_closure_warnings); only the
        # sentence is shown here.
        lines.append(_wrap("  " + _warning))
    if out.get("worth_knowing_early"):
        lines.append(_wrap("  " + out["worth_knowing_early"]))
    if out.get("free_hours_going_unused"):
        lines.append(_wrap("  " + out["free_hours_going_unused"]))
    return lines


# TEMPORARY HEURISTIC (presentation): how many running projects `state` lists before it summarises the rest.
RUNNING_LISTED = 12


def _state_running(out):
    lines = []
    active = out.get("active") or {}
    lines.append("")
    lines.append("RUNNING (%d):" % len(active) if active else "RUNNING: nothing")
    listed = sorted(active.items())
    hidden = []
    if len(listed) > RUNNING_LISTED:
        # the ones with something to act on come first; the rest are summarised by what they wait on
        listed.sort(key=lambda item: (not (item[1].get("why_underfunded")
                                           or item[1].get("will_be_abandoned_in_years") is not None), item[0]))
        hidden = listed[RUNNING_LISTED:]
        listed = sorted(listed[:RUNNING_LISTED])
    for node_id, progress in listed:
        total = progress.get("founder_hours_total") or 0
        left = progress.get("founder_hours_left") or 0
        pct = 100.0 * (total - left) / total if total else 100.0
        # Clamped, as a defence independent of core.py's own arithmetic: a
        # negative or over-100% figure here would print an impossible
        # "your hours spent" percentage, so the display refuses to show
        # one either way.
        pct = max(0.0, min(100.0, pct))
        # THE ID, because that is what `stop` and `why` take: printing the
        # display NAME here instead would leave no way to map it back to
        # an id to act on. The name goes on the line after, where it costs
        # nothing.
        lines.append("  %-34s %3.0f%% of your hours spent, %s still owed - waiting on %s"
                 % (node_id, pct, _fmt_num(progress.get("still_to_pay")),
                    progress.get("waiting_on") or "-"))
        if progress.get("name"):
            lines.append("      %s" % progress["name"])
        if progress.get("why_underfunded"):
            lines.append("      %s" % progress["why_underfunded"])
        if progress.get("will_be_abandoned_in_years") is not None:
            _tr = progress.get("because_nobody_here_can") or ["trade"]
            lines.append("      !! ABANDONED IN %s YEAR%s unless you can find %s %s: "
                     "everything spent on it goes. 'stop %s' keeps your hours."
                     % (_fmt_num(progress["will_be_abandoned_in_years"]),
                        "" if progress["will_be_abandoned_in_years"] == 1 else "S",
                        "an" if _tr[0][0] in "aeiou" else "a",
                        " or ".join(_tr), node_id))
    if hidden:
        lines.append(_running_summary(hidden))
    return lines


def _running_summary(hidden):
    waits = {}
    for _node_id, progress in hidden:
        waits[progress.get("waiting_on") or "-"] = waits.get(progress.get("waiting_on") or "-", 0) + 1
    return ("  ... and %d more, waiting on %s ('portfolio' lists every one)"
            % (len(hidden), ", ".join("%s (%d)" % (kind, count) for kind, count in sorted(waits.items()))))


def _state_stuck(out):
    lines = []
    stuck = out.get("stuck")
    if stuck:
        lines.append("")
        lines.append("!! " + stuck["you_are_stuck"].upper())
        lines.append(_wrap(stuck["this_is_not_the_end_of_the_run"], indent="   "))
        for suggestion in stuck["what_would_change_it"]:
            lines.append(_wrap("- " + suggestion, indent="   "))
    return lines


def _state_concerns(out):
    lines = []
    idle_v = out.get("you_know_how_to_run_but_have_not_opened")
    if out.get("concerns_you_run") or idle_v:
        lines.append("")
        if out.get("shut_concerns_pointer_seen"):
            lines.append("RUNNING AS CONCERNS: %s   (%s shut: 'ventures')"
                     % (_fmt_num(out.get("concerns_you_run")), _fmt_num(idle_v)))
        else:
            lines.append("RUNNING AS CONCERNS: %s   (you know how to run %s more and "
                     "have not opened them - 'ventures')"
                     % (_fmt_num(out.get("concerns_you_run")), _fmt_num(idle_v)))
        if out.get("shut_concerns_would_earn_a_year"):
            lines.append("  those shut concerns would clear %s den/yr between them, "
                     "and earn nothing while they are shut"
                     % _fmt_num(out["shut_concerns_would_earn_a_year"]))
    if out.get("shut_for_want_of_staff"):
        lines.extend(render_shut_for_want_of_staff(out["shut_for_want_of_staff"]))
    return lines


def _state_employ(out):
    lines = []
    employees = out.get("employees") or {}
    lines.append("")
    _house = (out.get("slaves") or 0) + (out.get("freedmen") or 0)
    lines.append("EMPLOY: %s people, %s den/yr in wages%s"
             % (_fmt_num(out.get("employees_total")),
                _fmt_num(out.get("annual_wage_bill")),
                ("   (and %s in your household, owned or freed)" % _fmt_num(_house))
                if _house else ""))
    if out.get("household_places_used_of_all"):
        lines.append("  household places: %s used - what you can feed, house and "
                 "oversee. 'labour' says what raises it."
                 % out["household_places_used_of_all"])
    for trade, value in sorted(employees.items()):
        lines.append("  %-16s %s" % (trade, _fmt_num(value)))
    if not employees:
        lines.append("  nobody")
    if out.get("what_you_can_field"):
        lines.append(_wrap(out["what_you_can_field"], indent="  "))
    if out.get("staff_are_fractional_because"):
        lines.append(_wrap(out["staff_are_fractional_because"], indent="  "))
    return lines


def _state_living_stock(out):
    held = out.get("living_stock") or {}
    if not held:
        return []
    return ["", "LIVING STOCK HELD: " + ", ".join("%s %s" % (material, _fmt_num(units))
                                                for material, units in sorted(held.items()))]


def _state_standing(out):
    lines = []
    lines.append("")
    # PROTECTION BELONGS HERE: it is what bribes, patrons and standing
    # actually buy, and what decides whether a strange result out of your
    # workshop is read as learning or as sorcery. Leaving it off this
    # screen entirely would make it a hidden stat nothing visibly moves.
    lines.append("STANDING: reputation %s   protection %s   scandal %s   eminence %s"
             % (_fmt_num(out.get("reputation")), _pct(out.get("protection")),
                _fmt_num(out.get("scandal")), _fmt_num(out.get("eminence"))))
    prom = out.get("prominence") or {}
    if prom:
        # SAY WHICH NUMBER IT IS ABOUT: this sits directly under the row
        # showing reputation, protection, scandal and eminence, and refers
        # to eminence specifically - ambiguous placement here would read
        # as a contradiction against a different figure on the same row.
        # "CHANCE OF RUIN" MEANS "CHANCE SOMETHING HAPPENS", and only a
        # fifth of those somethings end the run - a single merged figure
        # would conflate two different risks. Print both figures.
        if out.get("scandal_danger") is not None:
            lines.append("  SCANDAL is dangerous above %s (%s chance of being "
                     "denounced this year, which ends the run; 'bribe' buys it "
                     "down and it falls a tenth a year on its own)"
                     % (_fmt_num(out["scandal_danger"]),
                        _pct(out.get("chance_of_being_denounced_this_year"))))
            # THE DIRECTION, not only the level. See _agent_state.
            if out.get("years_until_scandal_crosses_the_line") is not None:
                lines.append("    and RISING: up %s last year. At that rate you "
                         "cross the line in about %s year(s), and the chance "
                         "above is only true of where you stand today"
                         % (_fmt_num(out.get("scandal_rose_by_last_year")),
                            _fmt_num(out["years_until_scandal_crosses_the_line"])))
        lines.append("  EMINENCE is dangerous above %s (settles near %s if nothing "
                 "changes; %s chance something lands this year, of which %s "
                 "would end the run)"
                 % (_fmt_num(prom.get("dangerous_above")),
                    _fmt_num(prom.get("settles_at_if_nothing_changes")),
                    _pct(prom.get("chance_of_ruin_this_year")),
                    _pct(prom.get("chance_the_run_ENDS_this_year"))))
        if prom.get("the_one_lever") and (prom.get("now") or 0) > (
                prom.get("dangerous_above") or 1e9) * 0.6:
            lines.append(_wrap(prom["the_one_lever"], indent="    "))
    lines.append("  technologies: %s built by you, %s granted for free (%s total)"
             % (_fmt_num(out.get("done_earned")), _fmt_num(out.get("done_granted")),
                _fmt_num(out.get("done_count"))))
    return lines


def _state_knowledge_warning(out):
    return [""] + warning_lines(out.get("knowledge_loss_warning"), units_text.text_label("money", "denarii")) if out.get("knowledge_loss_warning") else []


def _state_conditions(out):
    rows = out.get("conditions")
    if not rows:
        return []
    return [""] + ["CONDITION: " + condition_line(row, units_text.rate_label("mass", "yr", "t/year")) for row in rows]


def _state_at_risk(out):
    lines = []
    at_risk = out.get("at_risk")
    knowledge_risk = out.get("knowledge_risk")
    lines.append("")
    if at_risk:
        lines.append("AHEAD: %s technologies at risk if a hazard lands, hedged by %s"
                 % (_fmt_num(at_risk.get("technologies_you_could_lose")),
                    at_risk.get("hedged_by") or "nothing yet"))
        if at_risk.get("happening_now"):
            lines.append("  HAPPENING NOW: %s" % ", ".join(at_risk["happening_now"]))
        lines.append("  %s more hazard(s) known ahead - %s"
                 % (_fmt_num(at_risk.get("hazards_still_ahead")), at_risk.get("in_full") or ""))
    elif knowledge_risk:
        lines.append("AHEAD: %s technologies at risk; a sacking that costs you "
                 "anything (%s of them do) takes %s, hedged by %s"
                 % (_fmt_num(knowledge_risk.get("technologies_at_risk")),
                    _pct(knowledge_risk.get("and_the_chance_a_sacking_costs_you_anything")),
                    _fmt_num(knowledge_risk.get("expected_technologies_lost_per_sacking")),
                    knowledge_risk.get("hedged_by") or "nothing yet"))
        for hazard in knowledge_risk.get("known_hazards_ahead") or []:
            yrs = hazard.get("years") or [0, 0]
            tag = "IN PROGRESS" if hazard.get("in_progress") else "%s-%s" % (yrs[0], yrs[-1])
            lines.append("  [%s] %s" % (tag, hazard.get("name")))
    return lines
