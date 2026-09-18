"""The big per-screen renderers split out of render.py: render_state (the
main position screen, ~300 lines on its own), render_why (one node's full
story), render_available and render_step, plus the row-building helpers
(_RESTS_SHORT, _cost_marker, _available_row) that render_available needs and
that render_path (in render_screens_small.py) borrows for its own table.
Pure presentation, same as every module in this split: nothing here touches
the live Sim - see render.py and ARCHITECTURE.md.
"""

from ..data import downstream_count, trade_family

from .util import _factor, _fmt_num, _fmt_range, _pct, _wrap
# DISPLAY_WIDTH is NOT imported here: cli.py patches engine.protocol.DISPLAY_WIDTH
# directly at runtime, so every reader of it in this file goes through the
# protocol module itself, live, rather than a plain name bound once at import
# time - see _wrap's own comment on this, in engine/proto/util.py.

# `downstream_count`, above, is never called by name in this file: it is
# imported and then immediately shadowed. `_available_row` and `render_why`
# each bind a LOCAL variable called `downstream_count` from the reply dict
# they are reading, and that local shadows the import for the rest of that
# function's body. This is the same shape ruff flags as F811 (redefinition
# of an unused name) that stood in the original render.py before this file
# was split out of it. It is confusing and it is what the code does; leave
# it alone rather than fixing it as part of an unrelated change. `trade_family`
# travels on the same import line and is not referenced by name anywhere in
# this file either - the string "trade_family" that appears below is a dict
# key, not this name.

def render_state(out):
    """A position, not a dict: year, money, what is running and what each
    thing is waiting on, who you employ, what is about to happen to you.

    Works on both the short state() and state(full=true), and on step()'s
    reply, which is this same shape with completed/events stitched on front.
    """
    lines = []
    year = out.get("year")
    lines.append("=" * 60)
    # WITH THE CLOCK ON IT. The horizon was in one help topic and in no reply
    # anyone reads every turn, so a tester met it only by overshooting it.
    left = out.get("years_left")
    lines.append(("YEAR %s%s" % (year, ("   (%s years to the horizon at %s)"
                                    % (_fmt_num(left), out.get("horizon_year")))
                             if left is not None else ""))
             if year is not None else "STATE")
    lines.append("=" * 60)
    if out.get("ended"):
        lines.append("")
        lines.append("*** THE RUN HAS ENDED: %s ***" % out.get("end_reason"))

    lines.append("")
    net_after = out.get("net_after_project_spend")
    net_plain = out.get("net_per_year")
    spend = out.get("project_spend_this_year")
    lines.append("Money: %s den" % _fmt_num(out.get("capital")))
    # BOTH NUMBERS, ALWAYS - NOT ONE HIDING THE OTHER. This used to print
    # net_after_project_spend alone whenever it was present, which is every
    # turn: it is capital in less what you owe, less whatever went into
    # projects THIS YEAR, so starting one expensive thing made the household
    # look about to go broke on the very turn it was investing soundly. A
    # play tester read that plunge on every build and could not tell "the
    # household is failing" from "the household just paid for a workshop"
    # without a second command (`money`) the tutorial never points at. The
    # recurring figure - what standing income clears with nothing new
    # started - is the honest one to watch, and it now prints on the same
    # line `state` is read from every turn instead of one command away.
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
    if out.get("in_bondage_for_debt"):
        lines.append("IN DEBT BONDAGE: %s years left owing %s den"
                 % (_fmt_num(out["in_bondage_for_debt"]), _fmt_num(out.get("debt_still_to_work_off"))))

    # WHETHER YOU AGE IS A FACT ABOUT THE GAME YOU ARE PLAYING, and the human
    # rendering did not carry it: a mortal run and an immortal one looked
    # identical here, though the menu asks you to choose between them and one
    # of them ends with everything you have not made permanent dying with you.
    _src = out.get("where_your_hours_come_from") or {}
    _dep = _src.get("deputies_who_direct_work_for_you") or 0
    # THE AGE, ON THE LINE THAT ALREADY SAYS DEAD OR ALIVE, not only inside a
    # log sentence from however many years ago: a normal-play tester in
    # mortal mode never saw an age anywhere but that one line in `events`.
    lines.append("You: %s%s, %s founder-hours free this year%s"
             % ("alive" if out.get("founder_alive") else
                ("DEAD (aged about %s at death, in %s)"
                 % (out.get("founder_died_aged"), out.get("founder_died_in"))
                 if out.get("founder_died_aged") is not None else "DEAD"),
                " and ageing" if out.get("founder_ages") else " (you do not age)",
                _fmt_num(out.get("founder_hours_available")),
                ("   (%s of your own, plus %s deputies directing work in your "
                 "name at %s hours each)"
                 % (_fmt_num(_src.get("you")), _fmt_num(_dep),
                    _fmt_num(_src.get("hours_each_deputy_adds"))))
                if _dep else ""))
    for _warning in (out.get("supervision_close_to_the_edge") or []):
        # EACH ENTRY IS A DICT (id/name/within/of/headline/...), not a bare
        # string - staffing_closure_warnings() returns structured rows so a
        # JSON caller gets the trade, the room and the fix command apart from
        # the prose. This human-text renderer wants only the sentence; a
        # bare `_w` here crashed `state` outright the moment any warning
        # actually fired ("can only concatenate str (not 'dict') to str"),
        # which nothing caught because the regression suite only ever called
        # staffing_closure_warnings() directly, never through render_state.
        lines.append(_wrap("  " + (_warning.get("headline") if isinstance(_warning, dict) else _warning)))
    if out.get("worth_knowing_early"):
        lines.append(_wrap("  " + out["worth_knowing_early"]))
    if out.get("free_hours_going_unused"):
        lines.append(_wrap("  " + out["free_hours_going_unused"]))

    active = out.get("active") or {}
    lines.append("")
    lines.append("RUNNING (%d):" % len(active) if active else "RUNNING: nothing")
    for node_id, progress in sorted(active.items(), key=lambda kv: kv[0]):
        total = progress.get("founder_hours_total") or 0
        left = progress.get("founder_hours_left") or 0
        pct = 100.0 * (total - left) / total if total else 100.0
        # Clamped. Refunded hours could once exceed hours spent, and a
        # playtester read the result off this very line: "-67% of your hours
        # spent". The arithmetic is fixed in core.py; the display refuses to
        # print an impossible figure either way.
        pct = max(0.0, min(100.0, pct))
        # THE ID, because that is what `stop` and `why` take. This printed the
        # display NAME, so a play tester with a project they wanted to abandon
        # had no way to name it: "no way to map a running project's display
        # name back to an id so you can stop it". The name goes on the line
        # after, where it costs nothing.
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

    stuck = out.get("stuck")
    if stuck:
        lines.append("")
        lines.append("!! " + stuck["you_are_stuck"].upper())
        lines.append(_wrap(stuck["this_is_not_the_end_of_the_run"], indent="   "))
        for suggestion in stuck["what_would_change_it"]:
            lines.append(_wrap("- " + suggestion, indent="   "))

    idle_v = out.get("you_know_how_to_run_but_have_not_opened")
    if out.get("concerns_you_run") or idle_v:
        lines.append("")
        lines.append("RUNNING AS CONCERNS: %s   (you know how to run %s more and "
                 "have not opened them - 'ventures')"
                 % (_fmt_num(out.get("concerns_you_run")), _fmt_num(idle_v)))
        if out.get("shut_concerns_would_earn_a_year"):
            lines.append("  those shut concerns would clear %s den/yr between them, "
                     "and earn nothing while they are shut"
                     % _fmt_num(out["shut_concerns_would_earn_a_year"]))

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

    lines.append("")
    # PROTECTION BELONGS HERE. It is what bribes, patrons and standing actually
    # buy, and what decides whether a strange result out of your workshop is
    # read as learning or as sorcery - and it appeared on no screen at all. A
    # weird-play tester found it only by noticing that bribing with no scandal
    # to answer still moved SOMETHING, and reported it as a hidden stat being
    # sold to them.
    lines.append("STANDING: reputation %s   protection %s   scandal %s   eminence %s"
             % (_fmt_num(out.get("reputation")), _pct(out.get("protection")),
                _fmt_num(out.get("scandal")), _fmt_num(out.get("eminence"))))
    prom = out.get("prominence") or {}
    if prom:
        # SAY WHICH NUMBER IT IS ABOUT. This line sat directly under the row
        # showing reputation, suspicion, scandal and eminence, and refers to the
        # LAST of those - so a break tester with suspicion pinned at 30 read
        # "dangerous above 26 ... 0% chance of ruin this year" as a flat
        # contradiction, and wrote the whole mechanic off as inert. It was
        # answering a question they had not asked.
        # "CHANCE OF RUIN" MEANT "CHANCE SOMETHING HAPPENS", and only a fifth
        # of those somethings end the run. A play tester survived two
        # confiscations, was ended by the third roll, and had this same line in
        # front of them before all three. Print both figures.
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

    if out.get("fog_of_war"):
        lines.append("")
        lines.append("Fog of war is on: you see the next step, never the road. "
                 "%s of your own built so far." % _fmt_num(out.get("done_earned")))
        if out.get("goal_in_words"):
            lines.append("Aiming at: %s%s" % (out["goal_in_words"],
                     ("  -- REACHED in %s AD" % out.get("goal_year"))
                     if out.get("goal_reached") else ""))
        # HOW MANY, NEVER HOW MANY OF HOW MANY. See the field's own comment
        # in _agent_state for why the total stays withheld until the run is
        # over.
        if out.get("on_the_road_to_the_goal_so_far") is not None:
            lines.append("On the road there so far: %s of its nodes"
                     % _fmt_num(out["on_the_road_to_the_goal_so_far"]))
    elif out.get("goal"):
        lines.append("")
        lines.append("Goal: %s%s" % (out["goal"],
                 ("  -- REACHED in %s AD" % out.get("goal_year")) if out.get("goal_reached") else ""))

    completed = out.get("completed")
    events = out.get("events")
    lost = out.get("lost")
    fdts = out.get("the_founder_died_this_step")
    if completed or events or lost or fdts:
        head = []
        # THE LOUDEST LINE IN THE REPLY, not one more EVENT line among sixty.
        # See _founder_death_info and the step handler's own comment on why
        # a multi-year step stops here rather than running on past it.
        if fdts:
            head.append("  *** THE FOUNDER HAS DIED, aged about %s, in %s ***"
                        % (fdts.get("aged_about"), fdts.get("year")))
        for record in completed or []:
            head.append("  %s %s: %s"
                        % ("THIS SOCIETY NOW HAS" if record.get("granted")
                           else "COMPLETED", record.get("year"), record.get("name")))
        for record in lost or []:
            head.append("  LOST %s: %s%s"
                        % (record.get("year"), record.get("name"),
                           " (restore brings it back for a fraction of the cost)"
                           if record.get("can_be_restored") else ""))
        for event in events or []:
            # "DURING 381", NOT "EVENT 381". step() captures the year at the
            # top, logs everything that happens during that year under it, and
            # increments at the end - so an event is stamped with the year being
            # LIVED THROUGH while the prompt underneath already reads the next
            # one. A player reproducing a disaster from a save read "EVENT 381"
            # beside a prompt saying 382, concluded the event had not fired, and
            # spent a while chasing that. The year is right; "EVENT 381" implied
            # "as of 381" when it means "in the course of 381". Said the other
            # way, the two screens stop contradicting each other - and nothing
            # in any save or log changes, which a shift of the stamped year
            # itself could not have promised.
            head.append("  DURING %s: %s" % (event.get("year"), event.get("message")))
        if out.get("stopped_early"):
            head.append("  " + out["stopped_early"])
        lines = head + [""] + lines if head else lines

    also = out.get("also_available")
    if also:
        lines.append("")
        lines.append("more: " + "; ".join(also))
    return "\n".join(lines)


# The short forms of the bands, so the column stays a column.


_RESTS_SHORT = {"almost everything": "ALL", "a great deal": "much",
                "a fair amount": "some", "a few things": "few",
                "a little": "1-3",
                "nothing else; this is worth having for itself": "-"}


def _cost_marker(e, purse):
    """A row you cannot pay for today gets its cost marked.

    "MOST RESTS ON THESE" heads its list with items at 230 to 1,580 denarii
    against an opening purse of 400, and a break tester followed it into
    CREDIT EXHAUSTED by year 106. The advice is right - those really are the
    nodes everything rests on - and the reader needs to know which of them
    they can act on this year.
    """
    cost = e.get("cost")
    if purse is None or not isinstance(cost, (int, float)):
        return ""
    return "" if cost <= purse else "*"


def _available_row(e, w=None, purse=None):
    # THE FLOOR SCALES WITH DISPLAY_WIDTH, NOT A BARE 34. render_available
    # already grows this per-table to fit the longest id on the page (see
    # its own comment on _w below), so a narrow default never truncated one;
    # this only gives a wide terminal the same extra breathing room _wrap
    # gets, and reproduces exactly 34 at DISPLAY_WIDTH's own old default
    # (76), so nothing here moves for a player who has changed nothing.
    if w is None:
        # LIVE, NOT A SNAPSHOT: see _wrap's own comment on DISPLAY_WIDTH,
        # in engine/proto/util.py, for why this goes through the protocol
        # module rather than the plain imported name.
        from .. import protocol as _protocol
        w = max(34, _protocol.DISPLAY_WIDTH - 42)
    hours = e.get("founder_hours", e.get("your_hours"))
    years = e.get("calendar_floor_years", e.get("least_years"))
    risk = e.get("risk", e.get("chance_of_failure"))
    downstream_count = e.get("downstream_count")
    rests = (_fmt_num(downstream_count) if downstream_count is not None
             else _RESTS_SHORT.get(e.get("how_much_rests_on_this"), "?"))
    # THE ID IS NOT DECORATION, IT IS THE NEXT THING YOU TYPE. Truncating it to
    # thirty characters meant the longest ids could not be copied out of the
    # table at all, and both a play tester and a break tester lost time to
    # `start` refusing an id the table had just printed - with the refusal
    # helpfully suggesting they use `available` to find valid ids. Names get
    # cut instead; nobody has to retype a name.
    staff = e.get("needs_staff") or "-"
    if e.get("short_of_staff"):
        staff += "*"
    return "%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s" % (
        w, (e.get("id") or ""), (e.get("name") or "")[:20],
        _fmt_num(e.get("cost")) + _cost_marker(e, purse),
        _fmt_num(hours), _fmt_num(years), _pct(risk),
        _fmt_range(e.get("earns_per_year")), _fmt_num(e.get("costs_per_year_after")),
        staff, rests)


def render_available(out):
    """A scannable table: every column aligned, sorted cheapest-first so the
    same eye scan works whether you are looking for a bargain or a subject.
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
    header = ("%-*s %-20s %9s %7s %5s %5s %8s %7s %6s %6s"
              % (_width, "ID", "NAME", "COST", "HOURS", "YEARS", "RISK", "EARNS/YR",
                 "UPKEEP", "STAFF", "RESTS"))

    if "subjects" in out:
        lines.append("%-24s %8s %10s %10s %10s" % ("SUBJECT", "THINGS", "CHEAPEST", "DEAREST", "AFFORD"))
        for summary_row in out["subjects"]:
            lines.append("%-24s %8s %10s %10s %10s" % (
                summary_row["subject"][:24], _fmt_num(summary_row["things"]), _fmt_num(summary_row["cheapest"]),
                _fmt_num(summary_row["dearest"]), _fmt_num(summary_row["you_could_pay_for"])))
        lines.append("")
        lines.append("CHEAPEST SIX RIGHT NOW, sorted by cost:")
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
    elif "available" in out and not out["available"]:
        # No column headings over no rows. A play tester read "1-0 matching
        # 'furnace'" above an empty table and could not tell whether the
        # search had failed or the game had.
        lines.append(out.get("nothing_matched")
                 or "Nothing you could begin today matches that.")
    elif "available" in out:
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

    # LEGEND, once, and only when a table was actually printed. "1a*" means
    # nothing to a reader who has not been told; the column exists to be read
    # at a glance and a glance does not include guessing.
    _shown = ((out.get("available") or []) + (out.get("cheapest_six") or [])
              + (out.get("most_rests_on_these") or []))
    if _shown:
        lines.append("")
        lines.append("  STAFF is the standing people it needs: 2s = two scholars, "
                 "1a = one craftsman.")
        if any(entry.get("short_of_staff") for entry in _shown if isinstance(entry, dict)):
            lines.append("  A * after STAFF means you do not have them yet - 'hire' "
                     "or 'train' first, or the work waits.")
        if _purse is not None and any(_cost_marker(entry, _purse) for entry in _shown
                                      if isinstance(entry, dict)):
            lines.append("  A * after COST means you could not raise it today: "
                     "between cash and credit you can put %s into a project."
                     % _fmt_num(_purse))

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
    return "\n".join(lines)


def render_why(out):
    """A page about one thing: what it needs, what it costs, what depends
    on it, and whether you could start it today.
    """
    lines = []
    title = "%s  [%s]" % (out.get("name"), out.get("id"))
    lines.append(title)
    lines.append("=" * min(78, len(title)))
    bits = []
    if out.get("cat"):
        bits.append(out["cat"])
    if out.get("confidence"):
        bits.append("confidence %s" % out["confidence"])
    if bits:
        lines.append(", ".join(bits))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))

    lines.append("")
    cost = out.get("cost") or {}
    # EVERY FACTOR THAT IS MULTIPLIED IN. opposition_factor - bribes, delay, a
    # provincial site, a front man, up to 1.3x for work this society dislikes -
    # was in the JSON and not on this line, so a break tester multiplied the
    # printed terms out for three nodes, got 240 against 258, 200 against 230
    # and 10,075 against 10,831, and reported an undisclosed overhead. Third
    # time this exact lesson has been learned on this exact line: a breakdown
    # that omits a term invites the check and then fails it.
    lines.append("COST: %s den total  (%s labour + %s materials + %s capital, then "
             "x%s your civ, x%s distance, x%s scarcity, x%s opposition, "
             "x%s prices)"
             % (_fmt_num(cost.get("total")), _fmt_num(cost.get("labour")),
                _fmt_num(cost.get("materials")), _fmt_num(cost.get("capital")),
                _factor(cost.get("civ_domain_factor")),
                _factor(cost.get("material_distance_factor")),
                _factor(cost.get("scarce_material_premium")),
                _factor(cost.get("opposition_factor")),
                _factor(cost.get("price_index"))))
    if cost.get("already_paid_towards_this"):
        lines.append("!! %s den already sunk into this before it stopped: "
                 "'start' would actually charge %s den, not the total "
                 "above" % (_fmt_num(cost["already_paid_towards_this"]),
                            _fmt_num(cost.get("what_start_would_actually_charge"))))
    lines.append("YOUR HOURS: %s     CALENDAR FLOOR: %s years     FAILURE RISK: %s"
             % (_fmt_num(out.get("founder_hours")), _fmt_num(out.get("calendar_floor_years")),
                _pct(out.get("risk"))))
    if out.get("attempts_already_failed"):
        lines.append("ATTEMPTS ALREADY FAILED: %d. The risk above is what the next "
                 "attempt actually faces; it was %s before anyone tried. What "
                 "went wrong last time is not lost on the people who will try "
                 "again."
                 % (out["attempts_already_failed"],
                    _pct(out.get("risk_before_any_attempt"))))
    if out.get("failure_costs"):
        lines.append("IF IT FAILS: %s gone (40%% of the money) and %s of your "
                 "hours to do again. It can fail more than once."
                 % (_fmt_num(out.get("failure_costs")),
                    _fmt_num(out.get("failure_costs_hours"))))
    staff, have = out.get("staff_needed") or {}, out.get("you_have") or {}
    lines.append("STAFF NEEDED: %s scholars, %s artisans   (you have %s, %s%s)"
             % (_fmt_num(staff.get("scholars")), _fmt_num(staff.get("artisans")),
                _fmt_num(have.get("scholars")), _fmt_num(have.get("artisans")),
                (" - " + out["you_have_counts"]) if out.get("you_have_counts") else ""))
    for _k_warn in ("more_scholars_than_this_society_can_supply",
                    "more_craftsmen_than_your_household_can_hold"):
        if out.get(_k_warn):
            lines.append(_wrap("  !! " + out[_k_warn], indent="     "))
    # A SECOND, SEPARATE STAFF FIGURE. Not shown at all until `open` refused
    # somebody on it, which is the exact complaint three play testers filed.
    # See staff_to_keep_it_open_means for why this is not the line above.
    open_staff = out.get("staff_to_keep_it_open")
    if open_staff is not None:
        lines.append("STAFF TO KEEP IT OPEN: %s scholars, %s artisans   "
                 "(a share of their year, not a headcount - see below)"
                 % (_fmt_num(open_staff.get("scholars")),
                    _fmt_num(open_staff.get("artisans"))))
        if out.get("staff_to_keep_it_open_means"):
            lines.append(_wrap("  " + out["staff_to_keep_it_open_means"], indent="     "))
        if out.get("more_supervision_than_you_have_free_right_now"):
            lines.append(_wrap("  !! " + out["more_supervision_than_you_have_free_right_now"],
                            indent="     "))
        if out.get("these_are_a_share_of_their_year_not_a_headcount"):
            lines.append(_wrap("  " + out["these_are_a_share_of_their_year_not_a_headcount"],
                            indent="     "))
    lab = out.get("hired_labour") or {}
    if lab:
        lines.append("HIRED LABOUR: " + ", ".join("%s %sh" % (trade, _fmt_num(hours)) for trade, hours in lab.items()))
    mat = out.get("materials") or {}
    if mat:
        lines.append("MATERIALS: " + ", ".join("%s %s" % (material, _fmt_num(quantity)) for material, quantity in mat.items()))
    if out.get("upkeep") or out.get("revenue"):
        # A RANGE READS AS A RANGE, NOT AS TWO NUMBERS GLUED TOGETHER. See
        # _fog_revenue_estimate: under fog, on a thing nobody here has ever
        # run, this is a guess, and saying so is the whole point of showing
        # a guess instead of the true figure.
        _rev = out.get("revenue")
        _is_est = isinstance(_rev, (list, tuple))
        lines.append("UPKEEP: %s den/yr     REVENUE: %s den/yr%s"
                 % (_fmt_num(out.get("upkeep")), _fmt_range(_rev),
                    " (nobody has run this here yet - a guess, not a fact)"
                    if _is_est else ""))
    if out.get("but_it_pays_YOU") is not None:
        lines.append("  BUT IT PAYS YOU %s den/yr: %s"
                 % (_fmt_num(out["but_it_pays_YOU"]), out.get("because") or ""))
    if out.get("revenue_and_upkeep_apply_only_once_opened"):
        lines.append("  NOT CHARGED OR EARNED UNTIL YOU OPEN IT: finishing this "
                 "buys the knowledge; the figures above only start moving "
                 "once you 'open' it.")
    if out.get("this_is_a_capability_you_must_keep_open"):
        lines.append(_wrap("  KEEP THIS OPEN: " + out["this_is_a_capability_you_must_keep_open"],
                       indent="    "))

    lines.append("")
    status = ("DONE" if out.get("done") else
              "ACTIVE" if out.get("active") else
              "CAN START NOW" if out.get("can_start_now") else "BLOCKED")
    lines.append("STATUS: %s" % status)
    if out.get("active") and out.get("waiting_on"):
        lines.append(_wrap("  waiting on: " + out["waiting_on"], indent="    "))
    if out.get("active") and out.get("why_underfunded"):
        lines.append(_wrap("  " + out["why_underfunded"], indent="    "))
    if out.get("start_blocked_reason"):
        # start_blocked_reason is already the full, human-authored sentence -
        # when it is naming missing prerequisites (the common case) it says
        # so itself, and a second "MISSING PREREQUISITES: ..." line straight
        # after it was the same list twice, once wrapped in a sentence and
        # once bare. Show the sentence; it is the more complete of the two.
        lines.append(_wrap(out["start_blocked_reason"], indent="  "))
    else:
        missing = out.get("missing_prerequisites")
        direct = out.get("direct_prerequisites")
        if out.get("held_without_building_it"):
            lines.append("THIS SOCIETY ALREADY HAS THIS. You did not build it and "
                     "do not maintain it.")
            if direct:
                lines.append("  (%s is how somebody who did not have it would get "
                         "there)" % ", ".join(direct))
        elif missing:
            lines.append("MISSING PREREQUISITES: " + ", ".join(missing))
        elif direct:
            lines.append("PREREQUISITES (all met, and finished counts for ever): "
                     + ", ".join(direct))
        else:
            lines.append("PREREQUISITES: none, you can start this on arrival")
    # DONE, NOT MERELY OPEN - SAID ONCE, WHICHEVER BRANCH ABOVE ACTUALLY
    # FIRED. A tester wrote "nothing states whether a prerequisite must be
    # DONE or open"; it has always meant done, but the one sentence that used
    # to say so lived only in the `elif missing:` branch just above, which
    # start_blocked_reason (the common case - see its own comment) pre-empts
    # on every refusal that actually has missing prerequisites, so a player
    # who hit this refusal in the ordinary way never saw it at all. Printed
    # here instead, off the same `missing` list, it is reachable whichever of
    # the two branches actually wrote the list out.
    if out.get("missing_prerequisites"):
        lines.append("  (a prerequisite has to be FINISHED, not merely started, "
                 "and it stays finished: you need not keep it running.)")

    if out.get("chain_size") is not None:
        lines.append("")
        lines.append("STILL TO BUILD BEHIND IT: %s of %s nodes, %s of your hours, %s den, %s-year serial floor"
                 % (_fmt_num(out["chain_size"]),
                    _fmt_num(out.get("chain_size_counting_what_you_have_built")),
                    _fmt_num(out.get("chain_founder_hours")),
                    _fmt_num(out.get("chain_cost")), _fmt_num(out.get("critical_path_years"))))

    unlocks = out.get("unlocks")
    if unlocks:
        lines.append("")
        lines.append("DIRECTLY UNLOCKS: " + ", ".join(unlocks))
    downstream_count = out.get("downstream_count")
    if downstream_count is not None:
        lines.append("TOTAL DOWNSTREAM: %s thing(s) depend on this%s"
                 % (_fmt_num(downstream_count), " -- INCLUDING THE GOAL" if out.get("on_goal_path") else ""))
    elif out.get("how_much_rests_on_this"):
        lines.append("HOW MUCH RESTS ON THIS: %s" % out["how_much_rests_on_this"])

    if out.get("bounty_eligible_by_type"):
        lines.append("")
        lines.append("BOUNTY: yes, could be posted as a public prize")
    if out.get("trades_that_do_not_exist_here"):
        lines.append("")
        lines.append(_wrap(out.get("hired_labour_means") or ""))
        lines.append("TRADES NOT YET TAUGHT HERE: " + ", ".join(out["trades_that_do_not_exist_here"]))
    if out.get("trades_taught_but_nobody_here_to_do_them_yet"):
        lines.append("")
        lines.append("TAUGHT, BUT NOBODY HERE TO DO IT YET: "
                 + ", ".join(out["trades_taught_but_nobody_here_to_do_them_yet"]))
        lines.append(_wrap(out.get("trades_taught_but_nobody_here_means") or ""))
    if out.get("staff_needed_means"):
        lines.append(_wrap(out["staff_needed_means"]))
    return "\n".join(lines)


def render_step(out):
    # step()'s reply is completed/events stitched onto a full state() reply;
    # render_state already knows how to read completed/events off the front.
    return render_state(out)
