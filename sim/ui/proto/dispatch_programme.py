"""The programme command: a standing development programme run each year inside step."""

from .command_registry import command
from .programme import ANNUAL_HOURS_KEY, caps_text, is_set, state, target_text
from .programme_pause import PAUSE_KEYS, pauses_text
from .pursue import CAP_KEYS, FOG_REFUSAL, resolve_goal


def _number(raw, key):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, "%s must be a number" % key
    if value < 0 or value != value:
        return None, "%s cannot be negative" % key
    return value, None


def _target(sim, raw):
    """(target, error): a category of work, or a goal (id, name, or the current goal)."""
    text = "" if raw is None else str(raw).strip()
    nodes = sim.nodes
    categories = {str(node.get("cat", "")).lower() for node in nodes.values()}
    if text and text not in nodes and text.lower() in categories:
        return {"kind": "category", "value": text.lower()}, None
    if sim.fog:
        return None, FOG_REFUSAL + " A programme can follow a category instead: 'programme set <category>'."
    goal, error = resolve_goal(sim, text)
    return ({"kind": "goal", "value": goal}, None) if goal else (None, error)


def _describe(sim):
    programme = state(sim)
    if not programme.get("target"):
        return {"ok": True, "programme": None,
                "note": "no programme set; 'programme set <goal or category> max_annual_draw:<n> "
                        "reserve_cash:<n> max_total_cost:<n>' starts one"}
    return {"ok": True, "programme": {
        "target": target_text(sim, programme["target"]), "caps": caps_text(programme, sim),
        "paused": bool(programme.get("paused")), "committed_so_far": round(programme.get("committed", 0.0), 1),
        "hours_committed_so_far": round(programme.get("hours", 0.0), 1),
        "pauses": pauses_text(programme), "paused_because": programme.get("paused_by"),
        "runs": "each year inside step, before time passes, through rush (exclusions and caps apply)"}}


def _set(sim, cmd):
    target, error = _target(sim, cmd.get("target", cmd.get("goal", cmd.get("id"))))
    if error:
        return {"ok": False, "error": error}
    caps = {}
    for key in CAP_KEYS + (ANNUAL_HOURS_KEY,):
        if cmd.get(key) is not None:
            caps[key], error = _number(cmd[key], key)
            if error:
                return {"ok": False, "error": error}
    pauses = {}
    for key in PAUSE_KEYS:
        if cmd.get(key) is not None:
            pauses[key], error = _number(cmd[key], key)
            if error:
                return {"ok": False, "error": error}
    limit = cmd.get("limit")
    if limit is not None:
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            return {"ok": False, "error": "limit must be a whole number"}
        if limit < 1:
            return {"ok": False, "error": "limit must be at least 1"}
    programme = state(sim)
    same = programme.get("target") == target
    # Money committed is judged against the caps it was committed under; founder hours carry on with the target.
    kept_keys = ("hours", "hours_year") + (("committed", "started_ids") if programme.get("caps") == caps else ())
    kept = {key: programme[key] for key in kept_keys if same and key in programme}
    programme.clear()
    programme.update(target=target, caps=caps, limit=limit, paused=False, committed=0.0, pauses=pauses,
                     auto_resume=str(cmd.get("auto_resume")).lower() in ("true", "1", "yes", "on"))
    programme.update(kept)
    return dict(_describe(sim), note="programme set; it acts each year inside 'step'")


@command("programme", group="projects", aliases=("program",),
         summary="a standing plan that starts work every year",
         usage=["programme set <goal or category> max_annual_draw:<n> reserve_cash:<n> max_total_cost:<n> max_total_hours:<n> "
                "max_annual_hours:<n> pause_debt:<n> pause_war_risk:<share> pause_shortage:<share> auto_resume limit:<n>",
                "programme show", "programme pause", "programme resume", "programme clear"],
         options={"set": "start (or replace) the programme", "show": "what it is and has committed",
                  "pause": "stop it acting until resumed", "resume": "let it act again",
                  "clear": "remove it"},
         description="Each year inside 'step', before time passes, the programme starts what its goal's route "
                     "(or category) allows through 'rush', so every exclusion and cap applies; total cost counts "
                     "what it already committed. It does nothing while in debt, below its reserve_cash floor or "
                     "paused, and stops starting once the founder hours it committed reach max_total_hours (or "
                     "max_annual_hours for one year). pause_debt (money owed), pause_war_risk (yearly chance a "
                     "site is sacked, as 'risk' shows) and pause_shortage (share of planned work lost to a "
                     "standing material shortage) pause it when exceeded; it stays paused until 'programme "
                     "resume' unless set with auto_resume, which resumes it when the condition clears. The "
                     "step reply says what it did and why it did not. A goal programme is not available under fog.")
def _cmd_programme(sim, nodes, cmd, ended):
    action = str(cmd.get("action") or "show").lower()
    if action == "set":
        return _set(sim, cmd)
    if action == "show":
        return _describe(sim)
    if action == "clear":
        state(sim).clear()
        return {"ok": True, "programme": None, "note": "programme cleared"}
    if action in ("pause", "resume"):
        if not is_set(sim):
            return {"ok": False, "error": "no programme is set"}
        state(sim)["paused"] = action == "pause"
        state(sim)["paused_by"] = None
        return _describe(sim)
    return {"ok": False, "error": "say set, show, pause, resume or clear"}
