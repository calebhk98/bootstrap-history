"""Turning a JSON reply into the readable text `--pretty` and `play` print. Pure presentation: every function here reads an already-built reply dict and returns text, never touching the live Sim - see ARCHITECTURE.md."""

import json, re

from ..data import downstream_count, trade_family

from .score import _score_lines
from .util import _factor, _fmt_num, _fmt_range, _pct, _wrap
# DISPLAY_WIDTH is NOT imported here: cli.py patches engine.protocol.DISPLAY_WIDTH
# directly at runtime, so every reader of it in this file goes through the
# protocol module itself, live, rather than a plain name bound once at import
# time - see _wrap's own comment on this, in engine/proto/util.py.

def render_values(out):
    lines = ["WHAT THIS SOCIETY BELIEVES"]
    for row in out.get("values") or []:
        lines.append("  %-22s %7s  %s" % (row["field"], _factor(row["value"]),
                                      row.get("means") or ""))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return "\n".join(lines)


def render_capacity(out):
    lines = ["THE INDUSTRIAL DASHBOARD"]
    res = out.get("resources") or []
    if res:
        lines.append("")
        lines.append("  RESOURCES")
        lines.append("  %-14s %12s %12s %12s" % ("MATERIAL", "CAPACITY/YR",
                                             "DEMAND/YR", "SURPLUS/YR"))
        for row in res:
            lines.append("  %-14s %12s %12s %12s%s"
                     % (row["material"], _fmt_num(row["capacity_t_per_yr"]),
                        _fmt_num(row["demand_t_per_yr"]),
                        _fmt_num(row["surplus_t_per_yr"]),
                        "  SHORT" if row["surplus_t_per_yr"] < 0 else ""))
            if row.get("yield_note"):
                lines.append(_wrap(row["yield_note"], indent="      "))
    power = out.get("power") or {}
    lines.append("")
    lines.append("  POWER")
    tiers = power.get("power_tiers_you_have_discovered")
    if isinstance(tiers, list) and tiers:
        for tier in tiers:
            lines.append("    [%s] %s" % ("x" if tier["built"] else " ", tier["capability"]))
    else:
        lines.append("    nothing discovered yet")
    gen = power.get("generation_kw")
    if gen:
        lines.append("    generation: %s kW local + %s kW grid = %s kW total"
                 % (_fmt_num(gen["local_workshop_scale"]), _fmt_num(gen["grid_scale"]),
                    _fmt_num(gen["total"])))
        lines.append("    demand: %s kW" % _fmt_num(power.get("demand_kw")))
        reserve_margin = power.get("reserve_margin")
        lines.append("    reserve margin: %s"
                 % ("no demand yet" if reserve_margin is None else _pct(reserve_margin) if reserve_margin >= 0
                    else "SHORT by " + _pct(-reserve_margin)))
        if power.get("transmission_capacity_kw"):
            lines.append("    grid transmission capacity: %s kW"
                     % _fmt_num(power["transmission_capacity_kw"]))
        if power.get("mechanical_shaft_power_kw"):
            lines.append("    mechanical shaft power available: "
                     + ", ".join("%s %s kW" % (mechanism, _fmt_num(value))
                                 for mechanism, value in power["mechanical_shaft_power_kw"].items()))
        if power.get("electricity_is_the_binding_constraint"):
            lines.append("    ELECTRICITY IS THE BINDING CONSTRAINT this year "
                     "(throttle %s)" % _pct(power.get("throttle")))
    if power.get("waiting_on_workshop_scale_power"):
        lines.append("    waiting on workshop-scale power: "
                 + ", ".join(power["waiting_on_workshop_scale_power"]))
    if power.get("waiting_on_grid_scale_power"):
        lines.append("    waiting on the grid: " + ", ".join(power["waiting_on_grid_scale_power"]))
    if power.get("note"):
        lines.append(_wrap(power["note"], indent="    "))
    mines = (out.get("mines") or {}).get("mines_you_own")
    lines.append("")
    lines.append("  MINES  (see 'mines' for the full table)")
    if isinstance(mines, list) and mines:
        for row in mines:
            commissioned_year = row.get("commissioned_year")
            yr_s = "%d" % commissioned_year if isinstance(commissioned_year, (int, float)) else str(commissioned_year)
            lines.append("    %-10s (since %6s) raises %8s of %8s needed  "
                     "supplying: %s"
                     % (row["material"], yr_s,
                        _fmt_num(row.get("actual_output_t_per_yr")),
                        _fmt_num(row.get("material_demand_t_per_yr")),
                        "yes" if row.get("actually_supplying_demand") else "no"))
    else:
        lines.append("    none")
    port = out.get("portfolio") or []
    lines.append("")
    lines.append("  PROJECT PORTFOLIO")
    if port:
        for row in port:
            lines.append("    %-28s [%s]  %s hrs left, %s yrs left, risk %s"
                     % (row["name"], row["constraint"].replace("_", " "),
                        _fmt_num(row["founder_hours_left"]),
                        _fmt_num(row["calendar_years_left"]), _pct(row["chance_of_failure"])))
            lines.append(_wrap("waiting on: " + str(row["waiting_on"]), indent="      "))
    else:
        lines.append("    nothing in hand")
    spare = out.get("spare_capacity") or {}
    lines.append("")
    lines.append("  SPARE CAPACITY")
    lines.append("    founder-hours free this year: %s"
             % _fmt_num(spare.get("founder_hours_available")))
    fam = spare.get("spare_by_trade_family")
    if isinstance(fam, list) and fam:
        lines.append("    " + "; ".join("%s: %s free (%s hrs)"
                                    % (family_row["trade_family"], _fmt_num(family_row["spare_people_equivalent"]),
                                       _fmt_num(family_row["spare_hours_this_year"])) for family_row in fam))
    lines.append("    you could raise %s now; %s standing net/yr"
             % (_fmt_num(spare.get("you_could_raise_right_now")),
                _fmt_num(spare.get("standing_net_per_year"))))
    if spare.get("free_hours_going_unused"):
        lines.append(_wrap("  " + spare["free_hours_going_unused"]))
    return "\n".join(lines)


def render_materials(out):
    lines = ["MATERIAL STOCKS  (tonnes on hand; flows per year)",
         "  %-14s %10s %10s %10s %10s" %
         ("MATERIAL", "ON HAND", "YOUR FLOW", "DEMAND", "BUY/T")]
    for row in out.get("materials") or []:
        lines.append("  %-14s %10s %10s %10s %10s" %
                 (row.get("material"), _fmt_num(row.get("stock_on_hand_tonnes")),
                  _fmt_num(row.get("own_production_tonnes_per_year")),
                  _fmt_num(row.get("current_demand_tonnes_per_year")),
                  _fmt_num(row.get("buy_per_tonne"))))
    lines.append("  " + out.get("how_to_trade", ""))
    return "\n".join(lines)


def render_portfolio(out):
    lines = ["PROJECT PORTFOLIO"]
    rows = out.get("projects") or []
    lines.append("  %d active project%s, %s founder-hours available this year"
             % (out.get("active_project_count") or 0,
                "" if out.get("active_project_count") == 1 else "s",
                _fmt_num(out.get("founder_hours_available_this_year"))))
    if rows:
        for row in rows:
            _rank = row.get("pool_rank_this_year")
            _count = row.get("pool_active_count_this_year")
            _directed = row.get("hours_directed_this_year")
            lines.append("")
            lines.append("  %-28s [%s]%s" % (row["name"], row["constraint"].replace("_", " "),
                                         "  (allocate: %s hrs/yr)" % _fmt_num(_directed)
                                         if _directed else ""))
            lines.append("    this year: %s offered, %s effective, of %s hrs "
                     "total to go%s"
                     % (_fmt_num(row.get("hours_offered_this_year")),
                        _fmt_num(row.get("hours_effective_this_year")),
                        _fmt_num(row.get("founder_hours_total")),
                        ("  (priority #%s of %s active)" % (_rank, _count))
                        if _rank and _count else ""))
            lines.append(_wrap("waiting on: " + str(row.get("waiting_on")), indent="      "))
            if row.get("why_underfunded"):
                lines.append(_wrap(row["why_underfunded"], indent="      "))
    else:
        lines.append("  nothing in hand - 'available' or 'stuck' says what you "
                 "could begin today")
    trows = out.get("trade_hours_demand_vs_supply") or []
    lines.append("")
    lines.append("  TRADE-HOUR DEMAND VS SUPPLY THIS YEAR")
    if trows:
        for trade_row in trows:
            lines.append("    %-14s demand %8s   supply %8s%s"
                     % (trade_row["trade"], _fmt_num(trade_row["demand_hours_this_year"]),
                        _fmt_num(trade_row["supply_hours_this_year"]),
                        ("   OVERSUBSCRIBED - queued: " +
                         ", ".join(trade_row["projects_drawing_on_it"][:3]))
                        if trade_row["oversubscribed"] else ""))
    else:
        lines.append("    nothing active draws on a hired trade")
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return "\n".join(lines)


def render_economy(out):
    lines = ["THE ECONOMY"]
    lines.append("  price index %s   wage index %s   cost of living %s/yr"
             % (_factor(out.get("price_index")), _factor(out.get("wage_index")),
                _fmt_num(out.get("cost_of_living_a_year"))))
    lit = out.get("literacy") or {}
    lines.append("  literacy: general %s, elite %s"
             % (_pct(lit.get("general")), _pct(lit.get("elite"))))
    lines.append("  household places used: %s" % out.get("household_places_used_of_all"))
    if out.get("market_saturation"):
        lines.append("")
        lines.append(_wrap(out["market_saturation"], indent="  "))
    if out.get("materials_at_a_premium"):
        lines.append(_wrap(out["materials_at_a_premium"], indent="  "))
    moved = out.get("what_moved_most")
    if isinstance(moved, dict) and moved:
        lines.append("")
        lines.append("  WHAT HAS MOVED MOST")
        for span, vals in sorted(moved.items()):
            lines.append("    %s: price index %+.3f, wage index %+.3f, literacy %+.3f"
                     % (span.replace("_", " "), vals["price_index"],
                        vals["wage_index"], vals["literacy_general"]))
    if out.get("tracked_material_prices"):
        lines.append("")
        lines.append("  MATERIALS ABOVE BOOK PRICE")
        for row in out["tracked_material_prices"]:
            if row["price_factor_over_book"] > 1.01:
                lines.append("    %-10s %sx book" % (row["material"],
                                                 _factor(row["price_factor_over_book"])))
    return "\n".join(lines)


def render_changes(out):
    lines = ["WHAT CHANGED, %s to %s AD" % (out.get("from_year"), out.get("to_year"))]
    moved = out.get("moved") or {}
    lines.append("  price index %+.3f   wage index %+.3f   literacy %+.3f (general)"
             % (moved.get("price_index", 0.0), moved.get("wage_index", 0.0),
                moved.get("literacy_general", 0.0)))
    lines.append("  capital %s%s   revenue %s%s/yr   %s technologies completed"
             % ("+" if moved.get("capital", 0) >= 0 else "", _fmt_num(moved.get("capital")),
                "+" if moved.get("revenue", 0) >= 0 else "", _fmt_num(moved.get("revenue")),
                _fmt_num(moved.get("technologies_completed"))))
    bottleneck = out.get("bottleneck") or {}
    if bottleneck.get("then") != bottleneck.get("now"):
        lines.append("  bottleneck moved: %s -> %s" % (bottleneck.get("then"), bottleneck.get("now")))
    elif bottleneck.get("now"):
        lines.append("  bottleneck unchanged: %s" % bottleneck.get("now"))
    cap = out.get("capacity_gained_or_lost")
    if isinstance(cap, list) and cap:
        lines.append("  capacity: " + ", ".join(
            "%s %+.1f t/yr" % (row["material"], row["change_t_per_yr"]) for row in cap))
    for label, key in (("built", "technologies_completed"),
                       ("newly heard of", "technologies_newly_heard_of"),
                       ("opened", "concerns_opened"), ("closed", "concerns_closed")):
        value = out.get(key)
        if isinstance(value, list) and value:
            lines.append("  %s: %s" % (label, ", ".join(value)))
    events = out.get("notable_events")
    if isinstance(events, list) and events:
        lines.append("")
        lines.append("  NOTABLE EVENTS")
        for event in events:
            lines.append(_wrap("%d: %s" % (event["year"], event["message"]), indent="    "))
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


def render_money(out):
    lines = ["LEDGER"]
    lines.append("Capital: %s den     Revenue: %s den/yr" % (_fmt_num(out.get("capital")), _fmt_num(out.get("revenue"))))
    src = out.get("where_the_money_comes_from") or {}
    if src:
        lines.append("  from:")
        for raw_key, value in sorted(src.items(),
                           key=lambda kv: -(kv[1] if isinstance(kv[1], (int, float)) else 0)):
            # The engine's own rows are node ids and must stay verbatim; the
            # aggregate lines are marked with a leading underscore so they sort
            # and read as what they are rather than as technologies.
            label = raw_key[1:].replace("_", " ") if raw_key.startswith("_") else raw_key
            lines.append("    %-38s %s" % (label, _fmt_num(value)))
        lines.append("    %-38s %s" % ("(these add up to the revenue above)", ""))
        if out.get("still_building_up_custom"):
            lines.append(_wrap("STILL BUILDING UP: " + out["still_building_up_custom"],
                           indent="    "))
        if out.get("about_your_own_practice"):
            lines.append(_wrap("YOUR PRACTICE: " + out["about_your_own_practice"],
                           indent="    "))
        if out.get("the_market_you_sell_into"):
            lines.append(_wrap("THE MARKET: " + out["the_market_you_sell_into"],
                           indent="    "))
    costs = out.get("what_it_costs_you") or {}
    if costs:
        lines.append("Costs:")
        for raw_key, value in costs.items():
            if value is None:
                continue
            lines.append("  %-30s %s"
                     % (raw_key.lstrip("_").replace("_", " "), _fmt_num(value)))
    lines.append("Net/yr before the work in hand: %s   (recurring - `state` "
             "prints this same figure)     spent on projects last step: %s"
             % (_fmt_num(out.get("net_per_year")),
                _fmt_num(out.get("spent_on_projects_last_year"))))
    if out.get("net_after_project_spend") is not None:
        lines.append("Net/yr after it: %s   (one-off; `state` prints this too, "
                 "alongside the recurring figure above)"
                 % _fmt_num(out.get("net_after_project_spend")))
    lines.append("Credit limit: %s (%s used)     interest on arrears: %s     paid so far: %s"
             % (_fmt_num(out.get("credit_limit")),
                out.get("of_that_limit_you_have_used") or "none",
                _pct(out.get("interest_rate_on_arrears")),
                _fmt_num(out.get("interest_paid_in_total"))))
    if out.get("still_owed_on_work_in_hand"):
        lines.append("Still owed on work in hand: %s" % _fmt_num(out["still_owed_on_work_in_hand"]))
    return "\n".join(lines)


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


def render_mines(out):
    lines = ["YOUR OWN WORKINGS"]
    rows = out.get("mines_you_own")
    if isinstance(rows, list) and rows:
        lines.append("  %-9s %8s %10s %10s %6s %6s %10s" % (
            "MATERIAL", "SINCE", "RATED", "ACTUAL", "UTIL", "SUPPLY", "COST/YR"))
        for row in rows:
            commissioned_year = row.get("commissioned_year")
            yr_s = "%d" % commissioned_year if isinstance(commissioned_year, (int, float)) else str(commissioned_year)
            lines.append("  %-9s %8s %10s %10s %6s %6s %10s%s"
                     % (row["material"], yr_s,
                        _fmt_num(row.get("rated_capacity_t_per_yr")),
                        _fmt_num(row.get("actual_output_t_per_yr")),
                        row.get("utilization") or "-",
                        "yes" if row.get("actually_supplying_demand") else "no",
                        _fmt_num(row["costs_you_a_year"]),
                        "   (ready %s)" % _fmt_num(row["ready_in"])
                        if row.get("ready_in") else ""))
        lines.append("")
        lines.append("  they cost %s den/yr in all, against revenue of %s"
                 % (_fmt_num(out.get("they_cost_you_a_year_in_all")),
                    _fmt_num(out.get("your_revenue_is"))))
        lines.append("  shut one with 'close <material>' (shuts every working of "
                 "that material at once)")
    else:
        lines.append("  none")
    pend = out.get("still_being_sunk") or {}
    if pend:
        lines.append("")
        lines.append("  still being sunk: "
                 + ", ".join("%s (ready %s)" % (material, _fmt_num(ready_year))
                             for material, ready_year in pend.items()))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"], indent="  "))
    return "\n".join(lines)


def render_labour(out):
    if isinstance(out.get("trade"), dict):
        trade_detail = out["trade"]
        lines = ["TRADE: %s (%s)" % (trade_detail.get("trade"), trade_detail.get("kind"))]
        lines.append("exists here: %s" % trade_detail.get("exists_here"))
        lines.append("a year of one: %s den     wage: %s den/hr" % (_fmt_num(trade_detail.get("a_year_of_one")), _fmt_num(trade_detail.get("wage_per_hour"))))
        # THE HIRE YOU ARE CONTEMPLATING, NOT THE PRICE ABOVE. That price is
        # the market as it stands; hiring moves it, and wage_bill then
        # charges the new price to everyone of this trade you have, not
        # only the one you are adding.
        if trade_detail.get("hiring_moves_the_price"):
            lines.append("%ss ARE SCARCE ENOUGH HERE THAT HIRING ONE MOVES THE "
                     "PRICE: once hired, every %s you have costs %s den/yr, "
                     "not %s - so with %s on staff already, your wage bill "
                     "for %ss would go from %s to %s den/yr the moment you "
                     "do this, not just the new hire's share of it."
                     % (trade_detail.get("trade"), trade_detail.get("trade"),
                        _fmt_num(trade_detail.get("a_year_of_one_after_you_hire_one")),
                        _fmt_num(trade_detail.get("a_year_of_one")), _fmt_num(trade_detail.get("you_employ")),
                        trade_detail.get("trade"), _fmt_num(trade_detail.get("wage_bill_for_this_trade_now")),
                        _fmt_num(trade_detail.get("wage_bill_for_this_trade_after_hiring_one_more"))))
        elif trade_detail.get("a_year_of_one_after_you_hire_one") is not None:
            # QUIET WHEN THE MOVE IS ORDINARY. Hiring one more of almost any
            # trade nudges its price a little; this says so plainly but
            # without a banner, so the loud warning above stays meaningful
            # when it does appear.
            lines.append("hiring one more would make it %s den/yr"
                     % _fmt_num(trade_detail.get("a_year_of_one_after_you_hire_one")))
        lines.append("you employ: %s     the town can supply: %s hours"
                 % (_fmt_num(trade_detail.get("you_employ")),
                    _fmt_num(trade_detail.get("hours_the_market_can_supply"))))
        if trade_detail.get("you_employ_is_fractional_because"):
            lines.append(_wrap("  " + trade_detail["you_employ_is_fractional_because"], indent="     "))
        if trade_detail.get("hours_your_own_people_add"):
            lines.append("your own %ss add %s" % (trade_detail.get("trade"),
                                              _fmt_num(trade_detail.get("hours_your_own_people_add"))))
        if trade_detail.get("hours_you_could_still_commission"):
            lines.append("and an outside shop would take on %s more hours at a "
                     "premium ('commission'); you have bought %s"
                     % (_fmt_num(trade_detail.get("hours_you_could_still_commission")),
                        _fmt_num(trade_detail.get("hours_you_have_commissioned"))))
        lines.append("so %s hours a year are available to you in all"
                 % _fmt_num(trade_detail.get("hours_available_to_you_in_all")))
        if trade_detail.get("most_this_society_can_ever_supply") is not None:
            lines.append("HEADCOUNT CEILING: %s %ss in total, ever, at any price - "
                     "you have or are teaching %s"
                     % (_fmt_num(trade_detail["most_this_society_can_ever_supply"]),
                        trade_detail.get("trade"), _fmt_num(trade_detail.get("you_have_or_are_teaching"))))
            lines.append(_wrap("what widens it: " + str(trade_detail.get("what_widens_it") or ""),
                           indent="  "))
        if trade_detail.get("note"):
            lines.append(_wrap(trade_detail["note"]))
        return "\n".join(lines)
    lines = ["LABOUR", "ON YOUR STAFF:"]
    staff = out.get("on_your_staff")
    _shown = False
    if isinstance(staff, list) and staff:
        _shown = True
        for row in staff:
            lines.append("  %-16s %8s   %s den/yr each%s"
                     % (row["trade"], _fmt_num(row["you_employ"]),
                        _fmt_num(row["a_year_of_one"]),
                        "   (%s dearer than usual)" % row["dearer_than_usual_by"]
                        if row.get("dearer_than_usual_by") else ""))
    # PEOPLE YOU OWN OR HAVE FREED ARE YOUR HOUSEHOLD TOO. They are not
    # `employees` and so were never on this list: a weird-play tester bought
    # ten people and read "ON YOUR STAFF: nobody" and "EMPLOY: 0 people" while
    # the prompt said art 7, and concluded - reasonably - that the game had
    # lost track of their household. It had not; it was only showing one third
    # of it.
    if out.get("slaves"):
        _shown = True
        lines.append("  %-16s %8s   held, not paid a wage"
                 % ("people you own", _fmt_num(out.get("slaves"))))
    if out.get("freedmen"):
        _shown = True
        lines.append("  %-16s %8s   freed, and worth more for it"
                 % ("freedmen", _fmt_num(out.get("freedmen"))))
    if not _shown:
        lines.append("  nobody")
    if out.get("household_places_in_all") is not None:
        lines.append("")
        lines.append("HOUSEHOLD PLACES: %s of %s used, room for %s more"
                 % (_fmt_num(out.get("household_places_used")),
                    _fmt_num(out.get("household_places_in_all")),
                    _fmt_num(out.get("room_for_more_people"))))
        if out.get("what_raises_that_room"):
            lines.append(_wrap("  to make room: " + str(out["what_raises_that_room"]),
                           indent="  "))
        # THE OTHER CEILING, which is not room and cannot be built past. A
        # tester met it only inside a `hire` refusal in year 463 of a 500-year
        # game, and called it the single thing that decided the run.
        if out.get("and_how_many_of_the_lettered_trades_this_society_supplies"):
            lines.append(_wrap("  the lettered trades: "
                           + out["and_how_many_of_the_lettered_trades_this_society_supplies"],
                           indent="  "))
    lines.append("")
    lines.append("YOU COULD HIRE: " + (", ".join(out.get("you_could_hire_here") or []) or "nobody new"))
    if out.get("only_the_ones_you_taught"):
        lines.append("EXISTS ONLY BECAUSE YOU TAUGHT IT: "
                 + ", ".join(out["only_the_ones_you_taught"])
                 + "   (no market; teach more, or they come only from your own)")
    lines.append("MUST BE TAUGHT: " + (", ".join(out.get("do_not_exist_here") or []) or "none"))
    training = out.get("in_training")
    if training:
        lines.append("")
        lines.append("IN TRAINING:")
        for row in training:
            lines.append("  %s x%s, ready %s" % (row.get("trade"), _fmt_num(row.get("people")), row.get("ready_year")))
    lines.append("")
    lines.append("Total employed: %s     annual wage bill: %s den"
             % (_fmt_num(out.get("you_employ_in_total")), _fmt_num(out.get("annual_wage_bill"))))
    if out.get("staff_are_fractional_because"):
        lines.append(_wrap(out["staff_are_fractional_because"], indent="  "))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return "\n".join(lines)


def render_population(out):
    """The country, the one town this household actually reaches, and
    every trade's three numbers side by side - see population_report()
    (labour.py) for where every figure in this comes from.
    """
    lines = ["POPULATION: %s" % out.get("civilisation", "")]
    lines.append("country: %s people, %s%% urban (~%s urban dwellers)"
             % (_fmt_num(out.get("population")),
                _fmt_num(round((out.get("urban_fraction") or 0) * 100, 1)),
                _fmt_num(out.get("urban_population_estimate"))))
    town = out.get("the_town_you_actually_operate_in") or {}
    lines.append("the town you actually operate in: ~%s people (an estimate - see note below)"
             % _fmt_num(town.get("estimated_population")))
    lines.append("")
    lines.append("%-14s %14s %14s %10s %8s" % ("TRADE", "IN THE COUNTRY", "WITHIN REACH",
                                           "YOU EMPLOY", "% OF REACH"))
    for row in out.get("trades") or []:
        share = row.get("share_of_the_reachable_pool_you_employ")
        lines.append("%-14s %14s %14s %10s %8s"
                 % (row.get("trade"), _fmt_num(row.get("estimated_in_the_country")),
                    _fmt_num(row.get("within_your_reach")) if row.get("exists_here") else "-",
                    _fmt_num(row.get("you_employ")),
                    ("%.1f%%" % (share * 100)) if share is not None else "-"))
    if out.get("what_this_means"):
        lines.append("")
        lines.append(_wrap(out["what_this_means"]))
    return "\n".join(lines)


def render_ventures(out):
    """What you run and what you could. This fell through to the generic
    key/value dump, which prints a list of dicts as raw Python - a tester
    reported "ventures dumps raw Python dicts" and they were reading exactly
    that."""
    lines = ["CONCERNS"]
    free = out.get("people_free_to_run_something_new") or {}
    lines.append("free to put behind something new: %s scholars, %s craftsmen%s"
             % (_fmt_num(free.get("scholars")), _fmt_num(free.get("craftsmen")),
                "   (one of each of those is you)"
                if out.get("one_of_each_of_those_is_you") else ""))
    _hi = out.get("you_have_in_all") or {}
    _hh = out.get("held_in_all") or {}
    if _hi:
        lines.append("you have %s scholars and %s craftsmen in all; %s and %s of "
                 "them are watching a concern"
                 % (_fmt_num(_hi.get("scholars")), _fmt_num(_hi.get("craftsmen")),
                    _fmt_num(_hh.get("scholars")), _fmt_num(_hh.get("craftsmen"))))
    _holders = out.get("and_these_concerns_are_holding_the_rest")
    if isinstance(_holders, list) and _holders:
        lines.append("")
        lines.append("  %-34s %10s %10s" % ("HELD BY", "SCHOLARS", "CRAFTSMEN"))
        for row in _holders:
            lines.append("  %-34s %10s %10s"
                     % (row["id"], _fmt_num(row["scholars"]), _fmt_num(row["craftsmen"])))
    if out.get("these_are_not_interchangeable"):
        lines.append("")
        lines.append(_wrap(out["these_are_not_interchangeable"], indent="  "))
    if out.get("these_are_a_share_of_their_year_not_a_headcount"):
        lines.append("")
        lines.append(_wrap(out["these_are_a_share_of_their_year_not_a_headcount"],
                       indent="  "))
    lines.append("")
    run = out.get("running")
    lines.append("RUNNING")
    if isinstance(run, list) and run:
        lines.append("  %-34s %10s %10s %8s" % ("ID", "EARNS/YR", "COSTS/YR", "NEEDS"))
        for row in run:
            needs = row.get("needs") or {}
            lines.append("  %-34s %10s %10s %4s sch %3s cr%s"
                     % (row.get("id"), _fmt_num(row.get("earns_a_year")),
                        _fmt_num(row.get("costs_a_year")),
                        _fmt_num(needs.get("scholars")), _fmt_num(needs.get("craftsmen")),
                        "   [CAPABILITY - see below]" if row.get("capability") else ""))
            foreman = row.get("specialist_foreman") or {}
            if foreman:
                lines.append("      specialist foreman: %s %s FTE"
                         % (_fmt_num(foreman.get("fte")), foreman.get("trade")))
    else:
        lines.append("  nothing")
    idle = out.get("you_know_how_but_have_not_opened")
    lines.append("")
    lines.append("YOU KNOW HOW, AND HAVE NOT OPENED  (ordinary earn/cost businesses)")
    if isinstance(idle, list) and idle:
        lines.append("  %-34s %10s %10s %10s" % ("ID", "EARNS/YR", "COSTS/YR", "TO OPEN"))
        for row in idle:
            lines.append("  %-34s %10s %10s %10s"
                     % (row.get("id"), _fmt_num(row.get("earns_a_year")),
                        _fmt_num(row.get("costs_a_year")), _fmt_num(row.get("to_open_it"))))
            foreman = row.get("specialist_foreman") or {}
            if foreman:
                lines.append("      needs specialist foreman: %s %s FTE"
                         % (_fmt_num(foreman.get("fte")), foreman.get("trade")))
    else:
        lines.append("  nothing")
    if out.get("and_more_you_could_open"):
        lines.append("  ...and %s more" % _fmt_num(out["and_more_you_could_open"]))
    # CAPABILITIES ARE NOT EARN/COST DECISIONS, and a table that scored them
    # as one is exactly what put identity_cover and patron_local in the same
    # row a Rome player could not tell apart. A separate heading, with money
    # figures still shown for reference but a standing warning that money is
    # not the whole story here.
    cap_idle = out.get("capabilities_you_know_how_to_run_but_have_not_opened")
    if isinstance(cap_idle, list) and cap_idle:
        lines.append("")
        lines.append("YOU KNOW HOW, AND HAVE NOT OPENED  (capabilities - NOT judged "
                 "on money alone; 'why <id>' says what each one actually does)")
        lines.append("  %-34s %10s %10s %10s" % ("ID", "EARNS/YR", "COSTS/YR", "TO OPEN"))
        for row in cap_idle:
            lines.append("  %-34s %10s %10s %10s"
                     % (row.get("id"), _fmt_num(row.get("earns_a_year")),
                        _fmt_num(row.get("costs_a_year")), _fmt_num(row.get("to_open_it"))))
    if out.get("your_practice_is_not_a_venture"):
        lines.append("")
        lines.append(_wrap("YOUR PRACTICE (not a concern, and not listed above): "
                       + out["your_practice_is_not_a_venture"]))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
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
    # AND WHICH OF THE THINGS IN FRONT OF YOU IS ONE OF THOSE. A playtester was
    # told the answer to the Spanish was "walls, firearms, powerful friends",
    # then played 154 years with 269 startable things in view and reported
    # finding no hedge of any kind. Naming the ones they can already see costs
    # nothing and is the difference between advice and a slogan.
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

    The generic renderer printed the warning below AFTER the list of eleven
    switches and their descriptions, unwrapped, as a single eighty-word line
    that a player scanning for a switch name would never read. The whole point
    of that paragraph is that it is read BEFORE somebody turns one on.
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
    # with the state as a word at the end of a name. An England play tester
    # read "auto_open ... opens concerns that plainly pay for themselves",
    # built a pawnshop that plainly paid for itself, watched nothing happen,
    # and wrote it up as the policy not matching its own description. The
    # screen was right - "off" was printed directly above that sentence - but
    # every description here is in the present indicative, so a reader
    # scanning descriptions reads eleven statements of what the game is doing
    # and has to carry a separate column in their head to know that ten of
    # them are hypothetical. Two headings cost nothing and remove the
    # ambiguity: what is running, and what is not.
    pol = out.get("policy") or {}
    does = out.get("what_each_does") or {}
    on = [switch for switch in sorted(pol) if pol[switch]]
    off = [switch for switch in sorted(pol) if not pol[switch]]
    for head, keys, empty in (
            ("RUNNING NOW:", on, "  nothing is automatic just now: every one "
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
    today. See the op handler's own comment: two players asked for exactly
    this, and a third built their own script outside the game to get it.
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


_RENDERERS = {
    "policy": render_policy,
    "state": render_state, "step": render_step, "available": render_available,
    "why": render_why, "money": render_money, "ledger": render_money,
    "accounts": render_money, "labour": render_labour, "risk": render_risk,
    "hazards": render_risk, "ventures": render_ventures, "path": render_path,
    "mines": render_mines, "workings": render_mines,
    "stuck": render_stuck, "log": render_log, "history": render_log,
    "values": render_values, "rush": render_rush,
    "capacity": render_capacity, "industry": render_capacity,
    "materials": render_materials,
    "dashboard": render_capacity, "portfolio": render_portfolio,
    "economy": render_economy, "changes": render_changes,
    "population": render_population,
    "final": render_final, "score": render_score,
}


# A REPLY IS FULL OF WORKED EXAMPLES, and until now every one of them was
# JSON: 'more: knowledge_risk -> {"cmd":"risk"}'. That is exactly right when a
# script is reading, and exactly wrong in front of a person who has just been
# told to type words. The JSON payload itself must not change - it is the
# protocol - so the translation happens here, on the rendered text only, and
# only when the caller says the reader is typing.
TYPED_HINTS = False
# The short form used in the compact lines ("400 den", "net +12 den/yr"). Set
# alongside TYPED_HINTS by whichever front end is rendering; see MONEY_WORDS.
MONEY_SHORT = "den"


def _typed_form(obj):
    """One command dict written the way a person would type it."""
    command = obj.get("cmd")
    if not command:
        return None
    bits = [str(command)]
    if command == "policy" and isinstance(obj.get("set"), dict):
        for switch, value in obj["set"].items():
            bits += [str(switch), "on" if value else "off"]
        return " ".join(bits)
    for key in ("id", "topic", "trade", "what", "material", "subject", "group",
                "file", "path"):
        if obj.get(key) not in (None, "", False):
            bits.append(str(obj[key]))
    for key, word in (("find", "find"), ("search", "find"), ("afford", "afford"),
                      ("limit", "limit"), ("offset", "offset")):
        if obj.get(key) not in (None, "", False):
            bits += [word, _fmt_num(obj[key]) if key != "find" and key != "search"
                     else str(obj[key])]
    for key in ("years", "n", "hours", "amount"):
        if obj.get(key) not in (None, "", False):
            bits.append(_fmt_num(obj[key]))
    if obj.get("all") is True:
        bits.append("all")
    if obj.get("full") is True:
        bits.append("full")
    return " ".join(bits)


# Values may be a bare word rather than a literal: several hints are written as
# worked examples with a placeholder in them ({"cmd":"buy","what":"slaves",
# "n":N}), which is not valid JSON and so survived the first version of this
# untouched, in front of a person who had been told to type words.
_JSON_HINT = re.compile(r'\{"cmd"\s*:\s*"[a-z_]+"(?:\s*,\s*"[a-z_]+"\s*:\s*'
                        r'(?:"[^"]*"|-?[0-9.]+|true|false|[A-Za-z_][A-Za-z0-9_]*'
                        r'|\{[^{}]*\}))*\}')
_JSON_PAIR = re.compile(r'"([a-z_]+)"\s*:\s*("(?:[^"]*)"|-?[0-9.]+|true|false'
                        r'|[A-Za-z_][A-Za-z0-9_]*)')


def _typed_deep(obj):
    """to_typed_hints applied to every string a renderer is about to read.

    Keys are left alone: a field name is protocol, and only the values a
    person reads get rewritten. Same rule, and same reason, as
    _localise_money.
    """
    if isinstance(obj, str):
        return to_typed_hints(obj)
    if isinstance(obj, list):
        return [_typed_deep(item) for item in obj]
    if isinstance(obj, dict):
        return {field: _typed_deep(value) for field, value in obj.items()}
    return obj


def to_typed_hints(text):
    """Rewrite every {"cmd":...} example in rendered text as a typed command.
    Best-effort: anything that will not parse is left exactly as it was."""
    def sub(m):
        raw = m.group(0)
        try:
            obj = json.loads(raw)
        except ValueError:
            # A worked example with a placeholder in it. Read the pairs off
            # textually and keep the placeholder as the player sees it.
            obj = {}
            for key, val in _JSON_PAIR.findall(raw):
                obj[key] = val[1:-1] if val.startswith('"') else val
            if "cmd" not in obj:
                return raw
        return _typed_form(obj) or raw
    return _JSON_HINT.sub(sub, text)


_DEN_RE = re.compile(r"\bden\b")


def render_pretty(op, resp):
    """The human rendering of one reply. Never touches stdout or the JSON
    itself - see cli.py, which prints this to stderr alongside the unchanged
    JSON line, only when --pretty is on.

    Rendering is best-effort ON PURPOSE: a bug in a formatter must cost the
    formatting, never the session. The JSON already went to stdout by the
    time this is called, so the worst this function can do is print an
    apology instead of a pretty table.
    """
    # LIVE, NOT A SNAPSHOT: cmd_play sets engine.protocol.TYPED_HINTS and
    # .MONEY_SHORT directly (module attributes, not a call) once per session
    # - see DISPLAY_WIDTH's own comment in engine/proto/util.py for the same
    # pattern. Reading them back through the protocol module itself, instead
    # of the plain names this file's own assignments below bind, is what
    # makes that patch visible here after the split.
    from .. import protocol as _protocol
    TYPED_HINTS = _protocol.TYPED_HINTS
    MONEY_SHORT = _protocol.MONEY_SHORT
    try:
        if isinstance(resp, dict) and resp.get("ok") is False:
            err = render_error(resp)
            return to_typed_hints(err) if TYPED_HINTS else err
        renderer = _RENDERERS.get((op or "").strip().lower(), render_generic)
        # REWRITE THE HINTS BEFORE WRAPPING, NOT AFTER. This ran on the
        # finished page, so a paragraph wrapped at 76 columns around a long
        # {"cmd":"hire","trade":"smith","n":3} and then had it replaced by
        # `hire smith 3`, leaving a ragged half-width block wherever the game
        # explains what to type - which is most of the places it explains
        # anything. Wrapping the final words is the only way the line lengths
        # can be right.
        out = renderer(_typed_deep(resp) if TYPED_HINTS else resp)
        if MONEY_SHORT != "den":
            # "Money: 400 den" in a game counted in pence was the other half of
            # the currency work, and a tester duly reported "pence vs den mixed
            # throughout".
            out = _DEN_RE.sub(MONEY_SHORT, out)
        return to_typed_hints(out) if TYPED_HINTS else out
    except Exception as e:
        return "(could not render a readable view of this reply: %s: %s)" % (type(e).__name__, e)
