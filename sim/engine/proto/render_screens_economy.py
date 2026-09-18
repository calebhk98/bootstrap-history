"""The economic and production accounting screens split out of render.py:
render_capacity (the industrial dashboard), render_materials, render_portfolio,
render_economy, render_changes, render_money, render_mines, render_labour,
render_population and render_ventures - every `--pretty` screen that reports
a ledger, a stock, a flow or a table of people and trades, as opposed to a
narrative or a status line. Pure presentation, same as every module in this
split: nothing here touches the live Sim - see render.py and ARCHITECTURE.md.
"""

from .util import _factor, _fmt_num, _pct, _wrap

# render_capacity is split into one function per screen section - resources,
# power, mines, project portfolio, spare capacity - moved verbatim, in the
# same order they always ran in, concatenated by render_capacity itself,
# which decides nothing the pieces did not already decide. Each section
# returns its own LINES rather than a dict: the ordering between and within
# sections IS the output a player reads, and merging dicts the way
# _agent_state's own screens do would lose exactly that (see render_state,
# render_screens_big.py, for the same split on the `state` screen).

def _capacity_resources(out):
    lines = []
    res = out.get("resources") or []
    if not res:
        return lines
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
    return lines


def _capacity_power_tiers(power):
    lines = []
    tiers = power.get("power_tiers_you_have_discovered")
    if isinstance(tiers, list) and tiers:
        for tier in tiers:
            lines.append("    [%s] %s" % ("x" if tier["built"] else " ", tier["capability"]))
    else:
        lines.append("    nothing discovered yet")
    return lines


def _capacity_power_generation(power):
    lines = []
    gen = power.get("generation_kw")
    if not gen:
        return lines
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
    return lines


def _capacity_power_waiting(power):
    lines = []
    if power.get("waiting_on_workshop_scale_power"):
        lines.append("    waiting on workshop-scale power: "
                 + ", ".join(power["waiting_on_workshop_scale_power"]))
    if power.get("waiting_on_grid_scale_power"):
        lines.append("    waiting on the grid: " + ", ".join(power["waiting_on_grid_scale_power"]))
    if power.get("note"):
        lines.append(_wrap(power["note"], indent="    "))
    return lines


def _capacity_power(out):
    power = out.get("power") or {}
    lines = ["", "  POWER"]
    lines += _capacity_power_tiers(power)
    lines += _capacity_power_generation(power)
    lines += _capacity_power_waiting(power)
    return lines


def _capacity_mines(out):
    mines = (out.get("mines") or {}).get("mines_you_own")
    lines = ["", "  MINES  (see 'mines' for the full table)"]
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
    return lines


def _capacity_portfolio(out):
    port = out.get("portfolio") or []
    lines = ["", "  PROJECT PORTFOLIO"]
    if port:
        for row in port:
            lines.append("    %-28s [%s]  %s hrs left, %s yrs left, risk %s"
                     % (row["name"], row["constraint"].replace("_", " "),
                        _fmt_num(row["founder_hours_left"]),
                        _fmt_num(row["calendar_years_left"]), _pct(row["chance_of_failure"])))
            lines.append(_wrap("waiting on: " + str(row["waiting_on"]), indent="      "))
    else:
        lines.append("    nothing in hand")
    return lines


def _capacity_spare(out):
    spare = out.get("spare_capacity") or {}
    lines = ["", "  SPARE CAPACITY"]
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
    return lines


def render_capacity(out):
    lines = ["THE INDUSTRIAL DASHBOARD"]
    lines += _capacity_resources(out)
    lines += _capacity_power(out)
    lines += _capacity_mines(out)
    lines += _capacity_portfolio(out)
    lines += _capacity_spare(out)
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


# render_changes is split into one function per section, same reasoning and
# same order as render_capacity above.

def _changes_moved_lines(out):
    moved = out.get("moved") or {}
    lines = ["  price index %+.3f   wage index %+.3f   literacy %+.3f (general)"
             % (moved.get("price_index", 0.0), moved.get("wage_index", 0.0),
                moved.get("literacy_general", 0.0))]
    lines.append("  capital %s%s   revenue %s%s/yr   %s technologies completed"
             % ("+" if moved.get("capital", 0) >= 0 else "", _fmt_num(moved.get("capital")),
                "+" if moved.get("revenue", 0) >= 0 else "", _fmt_num(moved.get("revenue")),
                _fmt_num(moved.get("technologies_completed"))))
    return lines


def _changes_bottleneck_line(out):
    bottleneck = out.get("bottleneck") or {}
    if bottleneck.get("then") != bottleneck.get("now"):
        return ["  bottleneck moved: %s -> %s" % (bottleneck.get("then"), bottleneck.get("now"))]
    if bottleneck.get("now"):
        return ["  bottleneck unchanged: %s" % bottleneck.get("now")]
    return []


def _changes_capacity_line(out):
    cap = out.get("capacity_gained_or_lost")
    if isinstance(cap, list) and cap:
        return ["  capacity: " + ", ".join(
            "%s %+.1f t/yr" % (row["material"], row["change_t_per_yr"]) for row in cap)]
    return []


def _changes_tech_lines(out):
    lines = []
    for label, key in (("built", "technologies_completed"),
                       ("newly heard of", "technologies_newly_heard_of"),
                       ("opened", "concerns_opened"), ("closed", "concerns_closed")):
        value = out.get(key)
        if isinstance(value, list) and value:
            lines.append("  %s: %s" % (label, ", ".join(value)))
    return lines


def _changes_events_block(out):
    events = out.get("notable_events")
    lines = []
    if isinstance(events, list) and events:
        lines.append("")
        lines.append("  NOTABLE EVENTS")
        for event in events:
            lines.append(_wrap("%d: %s" % (event["year"], event["message"]), indent="    "))
    return lines


def render_changes(out):
    lines = ["WHAT CHANGED, %s to %s AD" % (out.get("from_year"), out.get("to_year"))]
    lines += _changes_moved_lines(out)
    lines += _changes_bottleneck_line(out)
    lines += _changes_capacity_line(out)
    lines += _changes_tech_lines(out)
    lines += _changes_events_block(out)
    return "\n".join(lines)


# render_money is split into one function per section, same reasoning and
# same order as render_capacity above.

def _money_header_line(out):
    return ["Capital: %s den     Revenue: %s den/yr" % (_fmt_num(out.get("capital")), _fmt_num(out.get("revenue")))]


def _money_from_block(out):
    src = out.get("where_the_money_comes_from") or {}
    lines = []
    if not src:
        return lines
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
    return lines


def _money_costs_block(out):
    costs = out.get("what_it_costs_you") or {}
    lines = []
    if not costs:
        return lines
    lines.append("Costs:")
    for raw_key, value in costs.items():
        if value is None:
            continue
        lines.append("  %-30s %s"
                 % (raw_key.lstrip("_").replace("_", " "), _fmt_num(value)))
    return lines


def _money_net_lines(out):
    lines = ["Net/yr before the work in hand: %s   (recurring - `state` "
             "prints this same figure)     spent on projects last step: %s"
             % (_fmt_num(out.get("net_per_year")),
                _fmt_num(out.get("spent_on_projects_last_year")))]
    if out.get("net_after_project_spend") is not None:
        lines.append("Net/yr after it: %s   (one-off; `state` prints this too, "
                 "alongside the recurring figure above)"
                 % _fmt_num(out.get("net_after_project_spend")))
    return lines


def _money_credit_lines(out):
    lines = ["Credit limit: %s (%s used)     interest on arrears: %s     paid so far: %s"
             % (_fmt_num(out.get("credit_limit")),
                out.get("of_that_limit_you_have_used") or "none",
                _pct(out.get("interest_rate_on_arrears")),
                _fmt_num(out.get("interest_paid_in_total")))]
    if out.get("still_owed_on_work_in_hand"):
        lines.append("Still owed on work in hand: %s" % _fmt_num(out["still_owed_on_work_in_hand"]))
    return lines


def render_money(out):
    lines = ["LEDGER"]
    lines += _money_header_line(out)
    lines += _money_from_block(out)
    lines += _money_costs_block(out)
    lines += _money_net_lines(out)
    lines += _money_credit_lines(out)
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


# render_labour has two entirely separate screens behind one command - the
# one-trade detail view and the household overview - selected by whether
# `trade` is present, never both, so they are split into their own
# functions with nothing shared between them; render_labour itself only
# dispatches. The overview is then split further, one function per section,
# same reasoning and order as render_capacity above.

def _render_labour_trade(out):
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


def _labour_staff_block(out):
    lines = ["ON YOUR STAFF:"]
    staff = out.get("on_your_staff")
    shown = False
    if isinstance(staff, list) and staff:
        shown = True
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
        shown = True
        lines.append("  %-16s %8s   held, not paid a wage"
                 % ("people you own", _fmt_num(out.get("slaves"))))
    if out.get("freedmen"):
        shown = True
        lines.append("  %-16s %8s   freed, and worth more for it"
                 % ("freedmen", _fmt_num(out.get("freedmen"))))
    if not shown:
        lines.append("  nobody")
    return lines


def _labour_household_block(out):
    lines = []
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
    return lines


def _labour_hire_block(out):
    lines = ["", "YOU COULD HIRE: " + (", ".join(out.get("you_could_hire_here") or []) or "nobody new")]
    if out.get("only_the_ones_you_taught"):
        lines.append("EXISTS ONLY BECAUSE YOU TAUGHT IT: "
                 + ", ".join(out["only_the_ones_you_taught"])
                 + "   (no market; teach more, or they come only from your own)")
    lines.append("MUST BE TAUGHT: " + (", ".join(out.get("do_not_exist_here") or []) or "none"))
    return lines


def _labour_training_block(out):
    lines = []
    training = out.get("in_training")
    if training:
        lines.append("")
        lines.append("IN TRAINING:")
        for row in training:
            lines.append("  %s x%s, ready %s" % (row.get("trade"), _fmt_num(row.get("people")), row.get("ready_year")))
    return lines


def _labour_totals_block(out):
    lines = ["", "Total employed: %s     annual wage bill: %s den"
             % (_fmt_num(out.get("you_employ_in_total")), _fmt_num(out.get("annual_wage_bill")))]
    if out.get("staff_are_fractional_because"):
        lines.append(_wrap(out["staff_are_fractional_because"], indent="  "))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return lines


def _render_labour_overview(out):
    lines = ["LABOUR"]
    lines += _labour_staff_block(out)
    lines += _labour_household_block(out)
    lines += _labour_hire_block(out)
    lines += _labour_training_block(out)
    lines += _labour_totals_block(out)
    return "\n".join(lines)


def render_labour(out):
    if isinstance(out.get("trade"), dict):
        return _render_labour_trade(out)
    return _render_labour_overview(out)


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


# render_ventures is split into one function per section, same reasoning
# and same order as render_capacity above.

def _ventures_summary(out):
    lines = []
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
    return lines


def _ventures_held_by_block(out):
    lines = []
    holders = out.get("and_these_concerns_are_holding_the_rest")
    if isinstance(holders, list) and holders:
        lines.append("")
        lines.append("  %-34s %10s %10s" % ("HELD BY", "SCHOLARS", "CRAFTSMEN"))
        for row in holders:
            lines.append("  %-34s %10s %10s"
                     % (row["id"], _fmt_num(row["scholars"]), _fmt_num(row["craftsmen"])))
    return lines


def _ventures_scope_notes_block(out):
    lines = []
    if out.get("these_are_not_interchangeable"):
        lines.append("")
        lines.append(_wrap(out["these_are_not_interchangeable"], indent="  "))
    if out.get("these_are_a_share_of_their_year_not_a_headcount"):
        lines.append("")
        lines.append(_wrap(out["these_are_a_share_of_their_year_not_a_headcount"],
                       indent="  "))
    return lines


def _ventures_running_block(out):
    lines = ["", "RUNNING"]
    run = out.get("running")
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
    return lines


def _ventures_idle_block(out):
    lines = ["", "YOU KNOW HOW, AND HAVE NOT OPENED  (ordinary earn/cost businesses)"]
    idle = out.get("you_know_how_but_have_not_opened")
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
    return lines


def _ventures_capabilities_block(out):
    """CAPABILITIES ARE NOT EARN/COST DECISIONS, and a table that scored them
    as one is exactly what put identity_cover and patron_local in the same
    row a Rome player could not tell apart. A separate heading, with money
    figures still shown for reference but a standing warning that money is
    not the whole story here.
    """
    lines = []
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
    return lines


def _ventures_practice_block(out):
    lines = []
    if out.get("your_practice_is_not_a_venture"):
        lines.append("")
        lines.append(_wrap("YOUR PRACTICE (not a concern, and not listed above): "
                       + out["your_practice_is_not_a_venture"]))
    if out.get("note"):
        lines.append("")
        lines.append(_wrap(out["note"]))
    return lines


def render_ventures(out):
    """What you run and what you could. This fell through to the generic
    key/value dump, which prints a list of dicts as raw Python - a tester
    reported "ventures dumps raw Python dicts" and they were reading exactly
    that."""
    lines = ["CONCERNS"]
    lines += _ventures_summary(out)
    lines += _ventures_held_by_block(out)
    lines += _ventures_scope_notes_block(out)
    lines += _ventures_running_block(out)
    lines += _ventures_idle_block(out)
    lines += _ventures_capabilities_block(out)
    lines += _ventures_practice_block(out)
    return "\n".join(lines)
