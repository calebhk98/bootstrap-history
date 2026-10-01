"""Uncertain estimates of what an unfinished node needs (complaint 188).

With the option on, screens that quote a node's requirements show a guess
instead of the truth for: staff needed, staff to keep it open (and its
specialist foreman), hired labour hours per trade, money cost, founder hours
and the calendar floor. Only the display is fuzzy: start checks, hiring,
supervision and bills read the real numbers.

A shown value is real * (1 - a + b) with a and b uniform on [0, 1], drawn from
a hash of (game salt, actor, node, figure), so it is the same on every look,
survives save and load, and is independent per actor. The spread is scaled by
`spread`: full before the project starts, half at start, narrowing in
proportion to the founder hours spent, and nothing once the node is done.
Decoy trades (trades the node does not use) are listed with estimates until
the project starts.
"""
import random
import re

from .data import WAGES

DEFAULT_ACTOR = "player"
DECOY_LIMIT = 3
ESTIMATE_NOTE = ("Figures marked ~ are estimates, not measurements: you do not "
                 "yet know this work well. They tighten once you start it and "
                 "as the work is done. The checks at start and open use the "
                 "true needs.")


def enabled(sim):
    return bool(getattr(sim.state, "_fuzzy_estimates", False))


def salt(sim):
    """The per-game salt, drawn once from the game's seeded rng."""
    if not getattr(sim.state, "_fuzzy_salt", 0):
        sim.state._fuzzy_salt = sim.rng.getrandbits(30) + 1
    return sim.state._fuzzy_salt


def actor_of(sim, actor=None):
    return actor or getattr(sim, "viewer_actor_id", None) or DEFAULT_ACTOR


def _rng(sim, actor, node_id, key):
    return random.Random("fuzzy192|%d|%s|%s|%s" % (salt(sim), actor, node_id, key))


def spread(sim, node_id):
    """1 before the project starts, 0.5 at start, falling to 0 as hours are spent."""
    if node_id in sim.done:
        return 0.0
    progress_record = sim.active.get(node_id)
    if progress_record is None:
        return 1.0
    hours = sim.nodes[node_id]["ph"]
    fraction_done = 0.0
    if hours > 0:
        fraction_done = min(1.0, max(0.0, 1.0 - progress_record.get("ph_left", hours) / hours))
    return 0.5 * (1.0 - fraction_done)


def ratio(sim, node_id, key, actor=None):
    """shown / real for one figure."""
    rng = _rng(sim, actor_of(sim, actor), node_id, key)
    below, above = rng.random(), rng.random()
    return 1.0 - spread(sim, node_id) * (below - above)


def estimate(sim, node_id, key, real, digits, actor=None):
    if real is None or not real:
        return real
    shown = round(real * ratio(sim, node_id, key, actor), digits)
    return round(max(0.0, min(shown, 2.0 * real)), digits)


def decoy_hours(sim, node_id, actor=None):
    """{trade: estimated hours} for one to three trades the node does not use."""
    if node_id in sim.done or node_id in sim.active:
        return {}
    node = sim.nodes[node_id]
    rng = _rng(sim, actor_of(sim, actor), node_id, "decoys")
    candidates = sorted(trade for trade in WAGES if trade not in node["lab"])
    if not candidates:
        return {}
    count = min(len(candidates), 1 + int(rng.random() * DECOY_LIMIT))
    picked = rng.sample(candidates, count)
    typical = (sum(node["lab"].values()) / len(node["lab"])) if node["lab"] else (node["ph"] or 100.0)
    return {trade: round(typical * (0.2 + 1.3 * rng.random())) for trade in picked}


def hired_labour(sim, node_id, actor=None):
    """Estimated hours per trade, real trades and decoys mixed and sorted."""
    shown = {trade: estimate(sim, node_id, "lab." + trade, hours, 0, actor)
             for trade, hours in sim.nodes[node_id]["lab"].items()}
    shown.update(decoy_hours(sim, node_id, actor))
    return dict(sorted(shown.items()))


def staff_estimate(sim, node_id, kind, real, actor=None, prefix="staff"):
    return estimate(sim, node_id, "%s.%s" % (prefix, kind), real, 2, actor)


def _scale(sim, node_id, key, value, digits, actor=None):
    """A derived figure scaled by the same ratio as the figure it comes from."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return value
    return round(value * ratio(sim, node_id, key, actor), digits)


_COST_KEYS = ("total", "labour", "materials", "capital", "base_total",
              "what_start_would_actually_charge")


_VAGUE_NEED = ("you do not have what it takes to begin this yet (people, money or "
               "hours); 'start' names the exact need")


def _fuzz_messages(sim, node_id, out, actor):
    node = sim.nodes[node_id]
    for key, kind, real in (("more_scholars_than_this_society_can_supply", "scholars", node["sch"]),
                            ("more_craftsmen_than_your_household_can_hold", "artisans", node["art"])):
        text = out.get(key)
        if text:
            shown = staff_estimate(sim, node_id, kind, real, actor)
            out[key] = re.sub(r"^\S+ wanted", "~%s (est.) wanted" % shown, text, count=1)
    text = out.get("more_supervision_than_you_have_free_right_now")
    if text and out.get("staff_to_keep_it_open"):
        keep = out["staff_to_keep_it_open"]
        out["more_supervision_than_you_have_free_right_now"] = re.sub(
            r"the equivalent of \S+ scholars and \S+ artisans",
            "the equivalent of ~%s scholars and ~%s artisans (est.)"
            % (keep["scholars"], keep["artisans"]), text, count=1)
    reason = out.get("start_blocked_reason")
    if (reason and re.search(r"\d", reason) and not out.get("done") and not out.get("active")
            and not out.get("missing_prerequisites")):
        out["start_blocked_reason"] = _VAGUE_NEED
    for blocker in out.get("blockers") or []:
        if re.search(r"\d", blocker["text"]) and blocker["kind"] in ("specialists", "money"):
            blocker["text"] = _VAGUE_NEED


def fuzz_why(sim, node_id, out, actor=None):
    """Replace the exact requirement figures of a `why` reply with estimates."""
    if node_id in sim.done or not enabled(sim):
        return out
    node = sim.nodes[node_id]
    fuzzed = ["staff_needed", "hired_labour", "founder_hours", "calendar_floor_years", "cost"]
    out["staff_needed"] = {"scholars": staff_estimate(sim, node_id, "scholars", node["sch"], actor),
                           "artisans": staff_estimate(sim, node_id, "artisans", node["art"], actor)}
    keep = out.get("staff_to_keep_it_open")
    if keep:
        fuzzed.append("staff_to_keep_it_open")
        out["staff_to_keep_it_open"] = {
            "scholars": staff_estimate(sim, node_id, "scholars", keep["scholars"], actor, "keep"),
            "artisans": staff_estimate(sim, node_id, "artisans", keep["artisans"], actor, "keep")}
    foreman = out.get("specialist_foreman_to_keep_it_open")
    if foreman:
        out["specialist_foreman_to_keep_it_open"] = dict(
            foreman, fte=estimate(sim, node_id, "keep.foreman", foreman["fte"], 2, actor))
    out["hired_labour"] = hired_labour(sim, node_id, actor)
    out["founder_hours"] = estimate(sim, node_id, "hours", node["ph"], 0, actor)
    for key in ("calendar_floor_years", "nominal_calendar_floor_before_reputation"):
        if key in out:
            out[key] = _scale(sim, node_id, "floor", out[key], 2, actor)
    if "earliest_completion_years" in out:
        out["earliest_completion_years"] = _scale(sim, node_id, "floor", out["earliest_completion_years"], 2, actor)
        out["earliest_completion_year"] = round(sim.state.scenario.year + out["earliest_completion_years"], 1)
    if "expected_calendar_years_with_retries" in out:
        out["expected_calendar_years_with_retries"] = _scale(
            sim, node_id, "floor", out["expected_calendar_years_with_retries"], 2, actor)
    cost = dict(out.get("cost") or {})
    for key in _COST_KEYS:
        if key in cost:
            cost[key] = _scale(sim, node_id, "cost", cost[key], 1, actor)
    out["cost"] = cost
    out["failure_costs"] = _scale(sim, node_id, "cost", out.get("failure_costs"), 1, actor)
    out["failure_costs_hours"] = _scale(sim, node_id, "hours", out.get("failure_costs_hours"), 1, actor)
    if out.get("critical_path_years_remaining") is not None:
        out["critical_path_years_remaining"] = None
    _fuzz_messages(sim, node_id, out, actor)
    out["figures_are_estimates"] = fuzzed
    out["estimates_note"] = ESTIMATE_NOTE
    return out


def _staff_cell(sim, node_id, actor):
    node = sim.nodes[node_id]
    bits = ""
    if node["sch"]:
        bits += "~%gs" % round(staff_estimate(sim, node_id, "scholars", node["sch"], actor), 1)
    if node["art"]:
        bits += "~%ga" % round(staff_estimate(sim, node_id, "artisans", node["art"], actor), 1)
    return bits or "-"


def fuzz_row(sim, node_id, row, actor=None):
    """Estimate the requirement figures of one `available`/`path` row."""
    if node_id in sim.done:
        return
    node = sim.nodes[node_id]
    if isinstance(row.get("cost"), (int, float)):
        row["cost"] = _scale(sim, node_id, "cost", row["cost"], 1, actor)
    for key in ("failure_costs", "payback_years"):
        if row.get(key) is not None:
            row[key] = _scale(sim, node_id, "cost", row[key], 1, actor)
    for key in ("founder_hours", "your_hours"):
        if key in row:
            row[key] = estimate(sim, node_id, "hours", node["ph"], 0, actor)
    if "failure_costs_hours" in row:
        row["failure_costs_hours"] = _scale(sim, node_id, "hours", row["failure_costs_hours"], 1, actor)
    for key in ("calendar_floor_years", "least_years", "nominal_calendar_floor_before_reputation",
                "expected_calendar_years_with_retries"):
        if key in row:
            row[key] = _scale(sim, node_id, "floor", row[key], 2, actor)
    if "needs_staff" in row:
        row["needs_staff"] = _staff_cell(sim, node_id, actor)
    foreman = row.get("specialist_foreman")
    if isinstance(foreman, dict) and "fte" in foreman:
        row["specialist_foreman"] = dict(
            foreman, fte=estimate(sim, node_id, "keep.foreman", foreman["fte"], 2, actor))
    if "trades_needed" in row:
        row["trades_needed"] = sorted(set(row["trades_needed"]) | set(decoy_hours(sim, node_id, actor)))


def _walk_rows(sim, value, actor):
    found = False
    if isinstance(value, dict):
        node_id = value.get("id")
        if isinstance(node_id, str) and node_id in sim.nodes and any(
                key in value for key in ("cost", "needs_staff", "founder_hours", "your_hours")):
            fuzz_row(sim, node_id, value, actor)
            found = True
        for child in value.values():
            found = _walk_rows(sim, child, actor) or found
    elif isinstance(value, list):
        for child in value:
            found = _walk_rows(sim, child, actor) or found
    return found


def fuzz_start(sim, node_id, out, actor=None):
    """The start reply: hours and floor as estimates (spread already halved)."""
    node = sim.nodes[node_id]
    out["founder_hours_needed"] = estimate(sim, node_id, "hours", node["ph"], 0, actor)
    for key in ("calendar_floor_years", "nominal_calendar_floor_before_reputation",
                "expected_calendar_years_with_retries"):
        if key in out:
            out[key] = _scale(sim, node_id, "floor", out[key], 2, actor)
    if "today_you_could_not_open_this_when_it_is_done" in out:
        out["today_you_could_not_open_this_when_it_is_done"] = (
            "with today's staff you could not open it once it is finished; "
            "'why' shows the estimate of what keeping it open takes")
    out["figures_are_estimates"] = ["founder_hours_needed", "calendar_floor_years"]
    out["estimates_note"] = ESTIMATE_NOTE


def fuzz_reply(sim, command_name, cmd, out):
    """Entry point: rewrite a command reply in place when the option is on."""
    if not enabled(sim) or not isinstance(out, dict) or not out.get("ok"):
        return out
    if command_name == "why":
        node_id = out.get("id")
        if node_id in sim.nodes:
            fuzz_why(sim, node_id, out)
    elif command_name == "start":
        node_id = out.get("started")
        if node_id in sim.nodes:
            fuzz_start(sim, node_id, out)
    elif command_name in ("available", "path"):
        if _walk_rows(sim, out, None):
            out["figures_are_estimates"] = ["cost", "founder_hours", "calendar_floor_years",
                                            "needs_staff"]
            out["estimates_note"] = ESTIMATE_NOTE
    return out
