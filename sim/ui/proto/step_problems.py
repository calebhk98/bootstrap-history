"""What went wrong across a multi-year step, read off the events and yearly snapshots the step already made."""
from sim.engine.ui_port import closure

# Event kind (sim/refusal.py LogLine) to the problem it counts toward.
_PROBLEM_OF_KIND = {
    "credit_exhausted": "credit_exhausted",
    "credit_near_limit": "near_limit",
    "arrears_interest": "arrears",
    "arrears_closed_concerns": "arrears_closure",
    "creditors_took": "arrears_closure",
    "concerns_closed_unstaffed": "unstaffed_closure",
    "treasury_watching": "confiscation_warning",
    "state_noticed": "state_notice",
    "site_sacked": "sacking",
    "knowledge_lost": "sacking",
    "debt_bondage": "credit_exhausted",
}


def route_nodes(sim):
    """The goal's prerequisite closure, or an empty set when there is no goal."""
    goal = sim.view("goal")()["node"]
    if not goal or goal not in sim.view("tree_nodes")():
        return set()
    return closure(sim.view("tree_nodes")(), goal)


def route_startable(sim, route):
    """True/False whether any unfinished node on the goal route can be begun now; None with no route."""
    pending = [node_id for node_id in route if node_id not in sim.view("techniques_held")() and node_id not in sim.view("active_projects")()]
    if not pending:
        return None
    return any(sim.view("start_check")(node_id, False, None, False)[0] for node_id in pending)


def stalled_projects(sim):
    """Names of active projects that have been waiting on a trade nobody has."""
    return [sim.view("tree_nodes")()[node_id]["name"] for node_id, progress in sorted(sim.view("active_projects")().items())
            if progress.get("stalled_years", 0) > 0]


def _years(years):
    years = sorted(set(years))
    if len(years) > 3:
        return "%d to %d" % (years[0], years[-1])
    return ", ".join(str(year) for year in years)


def _lapsed_hedges(events):
    """Closed concerns named in the `lapsed_hedges` fact of the events, in first-seen order."""
    names = []
    for event in events:
        for name in (event.get("facts") or {}).get("lapsed_hedges") or ():
            if name not in names:
                names.append(name)
    return names


def step_problems(years_ran, snapshots, events, stalled):
    """A short list of problems that appeared or persisted over the years just run;
    empty for a single year, which the ordinary output already covers."""
    if years_ran < 2:
        return []
    by_kind = {}
    for event in events:
        problem = _PROBLEM_OF_KIND.get(event.get("event_kind"))
        if problem:
            by_kind.setdefault(problem, []).append(event["year"])
    problems = []
    stuck_years = [snap["year"] for snap in snapshots if snap.get("route_startable") is False]
    if stuck_years:
        problems.append("nothing startable on the route to the goal in %d of %d years (%s)"
                        % (len(stuck_years), years_ran, _years(stuck_years)))
    credit = by_kind.get("credit_exhausted")
    if credit:
        problems.append("credit exhausted, projects halted (%s)" % _years(credit))
    money_years = (by_kind.get("near_limit", []) + by_kind.get("arrears", [])
                   + by_kind.get("arrears_closure", []))
    if money_years:
        problems.append("in arrears or near the credit limit in %d of %d years"
                        % (len(set(money_years)), years_ran))
    closed = sum(len(snap.get("concerns_closed", ())) for snap in snapshots)
    if closed or by_kind.get("unstaffed_closure"):
        problems.append("%d concern%s closed" % (closed, "" if closed == 1 else "s"))
    for kind, text in (("confiscation_warning", "the treasury is eyeing your fortune"),
                       ("state_notice", "the state has taken notice of you"),
                       ("sacking", "a sacking or lost knowledge")):
        if by_kind.get(kind):
            problems.append("%s (%s)" % (text, _years(by_kind[kind])))
    lapsed = _lapsed_hedges(events)
    if lapsed:
        problems.append("hedges lapsed because these are closed: " + ", ".join(lapsed))
    if stalled:
        problems.append("%d project%s stalled waiting on trades nobody here has: %s"
                        % (len(stalled), "" if len(stalled) == 1 else "s", ", ".join(stalled[:3])))
    return problems


def problems_lines(problems):
    """The rendered block; empty when there is nothing to say."""
    if not problems:
        return []
    return ["  PROBLEMS OVER THESE YEARS:"] + ["    - " + text for text in problems]
