"""The why screen: one technology's full story, one block per field, assembled by render_why."""

from .render_screen_state import _render_sections
from .util import _factor, _fmt_num, _fmt_range, _pct, _wrap
from .render_screens_market import why_goods_market_lines
from .hazard_words import why_hazard_lines, why_standing_lines


def _why_header(out):
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
    return lines


def _est(out, key, value):
    """A figure, shown as "~N" when the reply marks that field as an estimate."""
    if key in (out.get("figures_are_estimates") or ()):
        return "~" + _fmt_num(value)
    return _fmt_num(value)


def _est_tag(out, key):
    return " (est.)" if key in (out.get("figures_are_estimates") or ()) else ""


def _why_cost(out):
    lines = []
    lines.append("")
    cost = out.get("cost") or {}
    # EVERY FACTOR THAT IS MULTIPLIED IN: opposition_factor - bribes, delay,
    # a provincial site, a front man, up to 1.3x for work this society
    # dislikes - must appear on this line, not only in the JSON, or a
    # player who multiplies the printed terms out finds a total that does
    # not match and reads it as an undisclosed overhead: a breakdown that
    # omits a term invites the check and then fails it.
    lines.append("COST: %s den total%s  (%s labour + %s capital, x%s your civ, x%s prices; "
             "+ %s for the materials you do not hold, at today's market prices; "
             "then x%s distance, x%s opposition)"
             % (_est(out, "cost", cost.get("total")), _est_tag(out, "cost"),
                _est(out, "cost", cost.get("labour")), _est(out, "cost", cost.get("capital")),
                _factor(cost.get("civ_domain_factor")), _factor(cost.get("price_index")),
                _est(out, "cost", cost.get("materials")),
                _factor(cost.get("material_distance_factor")),
                _factor(cost.get("opposition_factor"))))
    if cost.get("already_paid_towards_this"):
        lines.append("!! %s den already sunk into this before it stopped: "
                 "'start' would actually charge %s den, not the total "
                 "above" % (_fmt_num(cost["already_paid_towards_this"]),
                            _fmt_num(cost.get("what_start_would_actually_charge"))))
    return lines


def _why_hours_risk(out):
    lines = []
    lines.append("YOUR HOURS: %s%s     CALENDAR FLOOR (a minimum): %s years%s     FAILURE RISK: %s"
             % (_est(out, "founder_hours", out.get("founder_hours")), _est_tag(out, "founder_hours"),
                _est(out, "calendar_floor_years", out.get("calendar_floor_years")),
                _est_tag(out, "calendar_floor_years"), _pct(out.get("risk"))))
    if out.get("earliest_completion_years") is not None:
        lines.append("EARLIEST FINISH, no failures: %s years (around %s); the bill is paid in yearly "
                     "instalments that reputation does not shorten"
                     % (_fmt_num(out["earliest_completion_years"]), _fmt_num(out.get("earliest_completion_year"))))
    if out.get("attempts_already_failed"):
        lines.append("ATTEMPTS ALREADY FAILED: %d. The risk above is what the next "
                 "attempt actually faces; it was %s before anyone tried. What "
                 "went wrong last time is not lost on the people who will try "
                 "again."
                 % (out["attempts_already_failed"],
                    _pct(out.get("risk_before_any_attempt"))))
    if out.get("failure_costs"):
        lines.append("IF IT FAILS: %s gone (a share of the money you still pay) and %s of your "
                 "hours to do again. It can fail more than once."
                 % (_fmt_num(out.get("failure_costs")),
                    _fmt_num(out.get("failure_costs_hours"))))
    return lines


def _why_staff_needed(out):
    lines = []
    staff, have = out.get("staff_needed") or {}, out.get("you_have") or {}
    lines.append("STAFF NEEDED: %s scholars, %s artisans%s   (you have %s, %s%s)"
             % (_est(out, "staff_needed", staff.get("scholars")),
                _est(out, "staff_needed", staff.get("artisans")), _est_tag(out, "staff_needed"),
                _fmt_num(have.get("scholars")), _fmt_num(have.get("artisans")),
                (" - " + out["you_have_counts"]) if out.get("you_have_counts") else ""))
    for _k_warn in ("more_scholars_than_this_society_can_supply",
                    "more_craftsmen_than_your_household_can_hold"):
        if out.get(_k_warn):
            lines.append(_wrap("  !! " + out[_k_warn], indent="     "))
    return lines


def _why_staff_keep_open(out):
    lines = []
    # A SECOND, SEPARATE STAFF FIGURE: it must not sit hidden until `open`
    # refuses somebody on it. See staff_to_keep_it_open_means for why
    # this is not the line above.
    open_staff = out.get("staff_to_keep_it_open")
    if open_staff is not None:
        lines.append("STAFF TO KEEP IT OPEN: %s scholars, %s artisans%s   "
                 "(a share of their year, not a headcount - see below)"
                 % (_est(out, "staff_to_keep_it_open", open_staff.get("scholars")),
                    _est(out, "staff_to_keep_it_open", open_staff.get("artisans")),
                    _est_tag(out, "staff_to_keep_it_open")))
        foreman = out.get("specialist_foreman_to_keep_it_open")
        if foreman:
            lines.append("  SPECIALIST FOREMAN TO KEEP IT OPEN: %s %s FTE (generic artisans cannot "
                     "substitute; you have %s free now)"
                     % (_est(out, "staff_to_keep_it_open", foreman.get("fte")), foreman.get("trade"),
                        _fmt_num(foreman.get("free_now"))))
        if out.get("charge_to_open"):
            lines.append("  CHARGE TO OPEN: %s den, paid when you `open` it "
                         "(`quote open <id>` shows it too)"
                         % _fmt_num(out["charge_to_open"]))
        if out.get("staff_to_keep_it_open_means"):
            lines.append(_wrap("  " + out["staff_to_keep_it_open_means"], indent="     "))
        if out.get("more_supervision_than_you_have_free_right_now"):
            lines.append(_wrap("  !! " + out["more_supervision_than_you_have_free_right_now"],
                            indent="     "))
        if out.get("these_are_a_share_of_their_year_not_a_headcount"):
            lines.append(_wrap("  " + out["these_are_a_share_of_their_year_not_a_headcount"],
                            indent="     "))
    return lines


def _why_labour_materials(out):
    lines = []
    lab = out.get("hired_labour") or {}
    if lab:
        lines.append("HIRED LABOUR: " + ", ".join("%s %sh" % (trade, _est(out, "hired_labour", hours))
                                                for trade, hours in lab.items())
                     + _est_tag(out, "hired_labour"))
        if out.get("estimates_note"):
            lines.append(_wrap("  " + out["estimates_note"], indent="  "))
    rows = out.get("material_rows") or []
    if rows:
        lines.append("MATERIALS (tonnes; missing part priced at today's market):")
        for row in rows:
            years = row.get("years_of_supply_it_takes")
            lines.append("  %-22s need %s, hold %s, missing %s -> %s den%s"
                         % (row["material"], _fmt_num(row["needed_tonnes"]),
                            _fmt_num(row["held_tonnes"]), _fmt_num(row["missing_tonnes"]),
                            _fmt_num(row["cost_of_missing"]),
                            "  (market and your own output supply this in about %s years)"
                            % _fmt_num(years) if years and years > 1.0 else ""))
    elif out.get("materials"):
        lines.append("MATERIALS: " + ", ".join("%s %s" % (material, _fmt_num(quantity)) for material, quantity in out["materials"].items()))
    return lines


def _why_upkeep_revenue(out):
    lines = []
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
    return lines


def _why_status(out):
    lines = []
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
        # so itself, so a second "MISSING PREREQUISITES: ..." line here would
        # show the same list twice, once wrapped in a sentence and once
        # bare. Show the sentence; it is the more complete of the two.
        blockers = out.get("blockers") or []
        if blockers:
            for blocker in blockers:
                lines.append(_wrap("BLOCKED BY %s: %s" % (blocker["kind"].upper(), blocker["text"]),
                                   indent="  "))
        else:
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
    # FIRED: it has always meant done, but start_blocked_reason (the
    # common case - see its own comment) pre-empts the `elif missing:`
    # branch above on every refusal that actually has missing
    # prerequisites, so a sentence saying so living only in that branch
    # would never reach a player who hit this refusal the ordinary way.
    # Printed here instead, off the same `missing` list, it is reachable
    # whichever of the two branches actually wrote the list out.
    if out.get("missing_prerequisites"):
        lines.append("  (a prerequisite has to be FINISHED, not merely started, "
                 "and it stays finished: you need not keep it running.)")
    return lines


def _why_chain(out):
    lines = []
    if out.get("chain_size") is not None:
        lines.append("")
        floor_left = out.get("critical_path_years_remaining")
        if floor_left is None:
            floor_left = out.get("critical_path_years")
        lines.append("STILL TO BUILD BEHIND IT: %s of %s nodes, %s of your hours, %s den, "
                 "%s-year serial floor left (%s from scratch)"
                 % (_fmt_num(out["chain_size"]),
                    _fmt_num(out.get("chain_size_counting_what_you_have_built")),
                    _fmt_num(out.get("chain_founder_hours")),
                    _fmt_num(out.get("chain_cost")), _fmt_num(floor_left),
                    _fmt_num(out.get("critical_path_years"))))
    return lines


def _why_unlocks_downstream(out):
    lines = []
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
    return lines


def _why_trailing(out):
    lines = []
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
    return lines


def _why_benefit(out):
    lines = []
    benefit = out.get("benefit")
    if benefit:
        lines.append("")
        lines.append("BENEFIT")
        lines.append(_wrap("  permanent: %s" % benefit["permanent"]))
        lines.append(_wrap("  while open: %s" % benefit["while_open"]))
        lines.append(_wrap("  cost of opening: %s" % benefit["cost_of_opening"]))
        lines.append(_wrap("  if shut: %s" % benefit["if_shut"]))
    if out.get("rebuild"):
        lines.append("")
        lines.append(_wrap("REBUILD: %s" % out["rebuild"]))
    return lines


def _why_living_stock(out):
    """What you know apart from what you hold: a technique is learned, a herd is possessed."""
    gates = out.get("living_stock") or []
    if not gates:
        return []
    lines = [""]
    lines.append("KNOWLEDGE: %s - %s" % (out.get("name") or "this",
                                          "known" if out.get("done") else "not yet learned"))
    for gate in gates:
        route = ("brought by %s, or by trade" % gate["brought_by"] if gate.get("brought_by")
                 else "by trade, gift or expedition")
        lines.append(_wrap("HELD: %s %s of %s needed - %s"
                           % (gate["material"], _fmt_num(gate["held"]), _fmt_num(gate["needed"]),
                              "enough" if gate["held"] >= gate["needed"] else "not enough: " + route),
                           indent="  "))
    return lines


def render_why(out):
    """A page about one thing: what it needs, what it costs, what depends
    on it, and whether you could start it today.
    """
    return "\n".join(_render_sections(out, (
        _why_header, _why_cost, _why_hours_risk, _why_staff_needed,
        _why_staff_keep_open, _why_labour_materials, _why_upkeep_revenue,
        why_goods_market_lines, _why_status, _why_living_stock, _why_benefit, why_standing_lines,
        why_hazard_lines, _why_chain, _why_unlocks_downstream,
        _why_trailing,
    )))
