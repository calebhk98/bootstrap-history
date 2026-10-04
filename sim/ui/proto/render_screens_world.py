"""The `--pretty` screens for map, education, demography and divergence.
Pure presentation of the replies built by the screen_* modules."""

from .util import _fmt_num, _wrap


def _percent(fraction):
    return "-" if fraction is None else "%.2f%%" % (100 * fraction)


def _deposit_words(deposits):
    return ", ".join("%s (%s)" % (deposit["name"], deposit["metal"])
                     for deposit in deposits)


def render_map(out):
    base = out.get("you_are_based_at") or {}
    lines = ["MAP: %s" % out.get("civilisation", "")]
    lines.append("regions: %s" % ", ".join(out.get("regions") or []))
    lines.append("based at %s (%s), %s; ~%s people in the tile, ~%s in the town"
                 % (base.get("name"), base.get("region"), base.get("terrain"),
                    _fmt_num(base.get("people")), _fmt_num(base.get("town_people"))))
    lines.append("")
    lines.append("TILES YOU HOLD (%s)" % out.get("tiles_held"))
    lines.append("%-22s %10s %6s  %s" % ("PLACE", "PEOPLE", "DAYS", "TERRAIN / DEPOSITS"))
    for row in out.get("tiles") or []:
        days = "base" if row.get("is_your_base") else _fmt_num(row.get("days_from_your_base"))
        lines.append("%-22s %10s %6s  %s" % (row["name"], _fmt_num(row["people"]),
                                             days, row["terrain"]))
        if row.get("deposits"):
            lines.append("%41s deposits: %s" % ("", _deposit_words(row["deposits"])))
    if out.get("next_door"):
        lines.append("")
        lines.append("NEXT DOOR (%s)" % out.get("next_door_total"))
        for row in out["next_door"]:
            tail = ("; deposits: " + _deposit_words(row["deposits"])) if row.get("deposits") else ""
            lines.append("  %s, beside %s: %s%s" % (row["name"], row["beside"],
                                                     row["terrain"], tail))
    lines.append("")
    lines.append(_wrap(out.get("towns_note", "")))
    lines.append(_wrap(out.get("how", "")))
    return "\n".join(lines)


def render_education(out):
    literacy = out["literacy"]
    lines = ["EDUCATION"]
    for kind in ("general", "elite"):
        lines.append("%s literacy %s of a ceiling of %s (%s of the ceiling); next year %s"
                     % (kind, _percent(literacy[kind]), _percent(literacy[kind + "_ceiling"]),
                        _percent(literacy["share_of_ceiling_" + kind]),
                        _percent(literacy[kind + "_next_year"])))
    change = out.get("recent_change") or {}
    if "since_year" in change:
        lines.append("since %s: general %+.2f points, elite %+.2f points"
                     % (change["since_year"], 100 * change["general"], 100 * change["elite"]))
    lines.append("schooling flow %s (%s with printing, %s of the country has adopted it); "
                 "farm share of working hours %s"
                 % (_fmt_num(out["schooling_flow"]), _fmt_num(out["effective_schooling_flow"]),
                    _percent(out["printing_adopted"]), _percent(out["farm_share_of_hours"])))
    if out.get("literacy_limited_by"):
        lines.append("literacy growth is limited by: %s" % out["literacy_limited_by"])
    lines.append("")
    lines.append("SCHOOLS")
    for row in out.get("schools") or []:
        state = "running" if row["running"] else ("built, shut" if row["built"] else "not built")
        lines.append("  %-34s %-11s flow %s  pupils made literate next year %s"
                     % (row["name"], state, _fmt_num(row["flow_added"]),
                        _fmt_num(row.get("people_made_literate_next_year", 0))))
    lines.append("")
    lines.append("LITERATE TRADES (the most you can ever have, and how many you employ)")
    for row in out.get("literate_trades") or []:
        lines.append("  %-12s %8s %6s" % (row["trade"], _fmt_num(row["most_you_can_ever_have"]),
                                         _fmt_num(row["you_employ"])))
    for record in out.get("trainees") or []:
        lines.append("  training %s %s, ready in %s" % (_fmt_num(record["count"]), record["trade"],
                                                       record["ready_in_year"]))
    for note in out.get("not_held") or []:
        lines.append(_wrap("not held: " + note))
    return "\n".join(lines)


def render_commitments(out):
    goal = out["goal"]
    lines = ["GOAL: %s%s" % (goal.get("name") or "withheld until you learn it",
                            " (reached in %s)" % goal["year_reached"] if goal["reached"] else "")]
    literacy = out["literacy"]
    lines.append("literacy: general %s of a ceiling of %s, elite %s of %s"
                 % (_percent(literacy["general"]), _percent(literacy["general_ceiling"]),
                    _percent(literacy["elite"]), _percent(literacy["elite_ceiling"])))
    for row in out.get("secondary_goals") or []:
        lines.append("also watching: %s, %s of %s done%s" % (
            row.get("name") or "a goal you have not learned the name of", row["done"], row["total"],
            " (reached)" if row.get("reached") else ""))
    lines.append(out["secondary_goals_note"])
    reserve = out["reserve"]
    lines += ["", "RESERVE: %s craftsmen, %s scholars (policy reserve_staff %s)"
              % (reserve["craftsmen"], reserve["scholars"], "on" if reserve["policy_on"] else "off"),
              "", "INSTITUTIONS"]
    for row in out["institutions"]:
        lines.append("  %-40s %-7s units %s" % (row["name"], row["state"], _fmt_num(row["units"])))
    if not out["institutions"]:
        lines.append("  none built yet")
    return "\n".join(lines)


def render_demography(out):
    cohorts = out["cohorts"]
    lines = ["DEMOGRAPHY",
             "%s people: %s children, %s working age (%s), %s elderly"
             % (_fmt_num(out["population"]), _fmt_num(cohorts["children"]),
                _fmt_num(cohorts["working_age"]), _percent(out.get("working_age_share")),
                _fmt_num(cohorts["elderly"]))]
    last = out.get("last_year")
    if last:
        lines.append("last year: %s born%s, %s died%s, net migration %s; nutrition ratio %s"
                     % (_fmt_num(last["births"]),
                        " (%s per thousand)" % _fmt_num(last["births_per_thousand"]) if last.get("births_per_thousand") is not None else "",
                        _fmt_num(last["deaths"]),
                        " (%s per thousand)" % _fmt_num(last["deaths_per_thousand"]) if last.get("deaths_per_thousand") is not None else "",
                        _fmt_num(last.get("immigration", 0) - last.get("emigration", 0)),
                        _fmt_num(last["nutrition_ratio"])))
    else:
        lines.append("last year's births and deaths: none simulated yet in this session")
    lines.append("disease burden %s of the pre-industrial level; wage index %s"
                 % (_fmt_num(out["disease_burden"]), _fmt_num(out["wage_index"])))
    for event in out.get("epidemics_under_way") or []:
        lines.append("under way: %s (%s-%s)" % (event["name"], *event["years"]))
    shocks = out.get("recent_shocks") or []
    if shocks:
        lines.append("")
        lines.append("SHOCKS (years the population fell sharply)")
        for row in shocks[-8:]:
            lines.append("  %s: %s, %s deaths, nutrition ratio %s" % (
                row["year"], _percent(row["change_share"]), _fmt_num(row["deaths"]), _fmt_num(row["nutrition_ratio"])))
    recovery = out.get("recovery")
    if recovery:
        lines.append("")
        lines.append("RECOVERY: peak %s in %s (%s years ago), now %s below it" % (
            _fmt_num(recovery["peak_population"]), recovery["peak_year"],
            recovery["years_since_peak"], _percent(recovery["share_below_peak"])))
        if recovery["years_to_regain_peak_at_recent_rate"] is not None:
            lines.append("  about %s years to regain it at the recent rate (%s a year); %s" % (
                _fmt_num(recovery["years_to_regain_peak_at_recent_rate"]),
                _percent(recovery["recent_growth_rate"]), recovery["basis"]))
    lines.append("")
    lines.append("%-14s %14s %14s" % ("TRADE", "IN THE COUNTRY", "WITHIN REACH"))
    for row in out.get("trades") or []:
        lines.append("%-14s %14s %14s" % (
            row["trade"], _fmt_num(row["estimated_in_the_country"]),
            _fmt_num(row["within_your_reach"]) if row["exists_here"] else "-"))
    for note in out.get("not_held") or []:
        lines.append(_wrap("not held: " + note))
    return "\n".join(lines)


def _pair_line(label, pair):
    return "%-18s start %s, now %s" % (label, _fmt_num(pair["start"]), _fmt_num(pair["now"]))


def render_divergence(out):
    lines = ["DIVERGENCE: %s years since %s" % (out["years_elapsed"], out["start_year"]),
             _pair_line("population", out["population"]),
             _pair_line("wage index", out["wage_index"]),
             _pair_line("price index", out["price_index"]),
             _pair_line("general literacy", out["literacy_general"]),
             _pair_line("elite literacy", out["literacy_elite"])]
    territory = out["territory"]
    lines.append("territory: %s" % ("changed" if territory["changed"] else "unchanged"))
    built = out.get("technologies_you_built") or []
    lines.append("")
    lines.append("TECHNOLOGIES YOU BUILT (%d)" % len(built))
    for row in built[:20]:
        lines.append("  %s (%s)" % (row["name"], row["year"]))
    if len(built) > 20:
        lines.append("  ... and %d more (json lists all)" % (len(built) - 20))
    lines.append("")
    lines.append("DATED EVENTS")
    for row in out.get("dated_events") or []:
        lines.append("  %s-%s %-20s %s" % (*row["years"], row["status"], row.get("name", "(withheld)")))
    lines.append("")
    for note in out.get("cannot_know") or []:
        lines.append(_wrap("cannot know: " + note))
    return "\n".join(lines)
