"""What went wrong across a multi-year step, read off the events and yearly snapshots the step already made."""
from ..data import closure

# (lowercase marker in an event message, key) - first match wins per event.
_EVENT_KINDS = (
    ("credit exhausted", "credit_exhausted"),
    ("close to the limit", "near_limit"),
    ("of arrears", "arrears"),
    ("in arrears, so closed", "arrears_closure"),
    ("creditors took", "arrears_closure"),
    ("nobody left to keep an eye", "unstaffed_closure"),
    ("treasury is looking at your fortune", "confiscation_warning"),
    ("the state has noticed you", "state_notice"),
    ("a site is sacked", "sacking"),
    ("knowledge lost", "sacking"),
    ("bondage", "credit_exhausted"),
)
_LAPSED_MARK = "(lapsed: "


def route_nodes(sim):
    """The goal's prerequisite closure, or an empty set when there is no goal."""
    goal = sim.goal
    if not goal or goal not in sim.nodes:
        return set()
    return closure(sim.nodes, goal)


def route_startable(sim, route):
    """True/False whether any unfinished node on the goal route can be begun now; None with no route."""
    pending = [node_id for node_id in route if node_id not in sim.done and node_id not in sim.active]
    if not pending:
        return None
    return any(sim.can_start(node_id) for node_id in pending)


def stalled_projects(sim):
    """Names of active projects that have been waiting on a trade nobody has."""
    return [sim.nodes[node_id]["name"] for node_id, progress in sorted(sim.active.items())
            if progress.get("stalled_years", 0) > 0]


def _years(years):
    years = sorted(set(years))
    if len(years) > 3:
        return "%d to %d" % (years[0], years[-1])
    return ", ".join(str(year) for year in years)


def _lapsed_hedges(events):
    """Closed concerns named in 'lapsed' hedge notes, in first-seen order."""
    names = []
    for event in events:
        message = event["message"]
        start = message.find(_LAPSED_MARK)
        while start >= 0:
            end = message.find(" is closed)", start)
            if end < 0:
                break
            name = message[start + len(_LAPSED_MARK):end]
            if name not in names:
                names.append(name)
            start = message.find(_LAPSED_MARK, end)
    return names


def step_problems(years_ran, snapshots, events, stalled):
    """A short list of problems that appeared or persisted over the years just run;
    empty for a single year, which the ordinary output already covers."""
    if years_ran < 2:
        return []
    by_kind = {}
    for event in events:
        lowered = event["message"].lower()
        for marker, kind in _EVENT_KINDS:
            if marker in lowered:
                by_kind.setdefault(kind, []).append(event["year"])
                break
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
