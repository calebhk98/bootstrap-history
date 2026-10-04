"""The state screen's sections, defined once, and the views built from them: short by default, every section on `state full`, one section on `state <section>`."""

from .render_screen_state_blocks import (
    _state_header, _state_money, _state_founder, _state_conditions, _state_at_risk,
    _state_knowledge_warning, _state_running, _state_stuck, _state_concerns,
    _state_employ, _state_living_stock, _state_standing,
)
from .util import _fmt_num


def _state_goal(out):
    lines = []
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
    return lines


def _state_todo(out):
    """What the player can do right now, from what the reply already says."""
    active = out.get("active") or {}
    idle = out.get("you_know_how_to_run_but_have_not_opened")
    lines = ["", "WHAT YOU CAN DO NOW:",
             "  begin something: 'available' lists what you could start today, 'start <id>' begins one",
             "  " + (("%s running ('portfolio' lists them)" % _fmt_num(len(active)))
                     if active else "nothing is running yet")]
    if idle:
        lines.append("  %s concerns you know how to run are shut: 'ventures'" % _fmt_num(idle))
    lines.append("  let time pass: 'step <years>'; if you are not getting on: 'stuck'")
    return lines


# Every section of the full screen, in the order `state full` prints them.
SECTIONS = {
    "situation": (_state_header, _state_money, _state_founder, _state_conditions),
    "goal": (_state_goal,),
    "risks": (_state_at_risk, _state_knowledge_warning),
    "work": (_state_running, _state_stuck, _state_concerns),
    "staff": (_state_employ, _state_living_stock),
    "standing": (_state_standing,),
}

# The short default: the situation and stock in hand, the bottleneck, what to do, the goal, the risks.
SHORT_BLOCKS = (SECTIONS["situation"] + (_state_living_stock, _state_stuck, _state_todo)
                + SECTIONS["goal"] + SECTIONS["risks"])


def _run(out, blocks):
    lines = []
    for block in blocks:
        lines += block(out)
    return lines


def render_view(out, view):
    """The lines for one view: None or "full" is every section, "short" the
    default, a section name just that section."""
    if view == "short":
        lines = _run(out, SHORT_BLOCKS)
        if not any(line.strip() for line in _run(out, SECTIONS["risks"])):
            lines += ["", "AHEAD: no known risks"]
        return lines + ["", "more: 'state full' for everything, or 'state <section>': %s"
                        % ", ".join(SECTIONS)]
    if view in SECTIONS:
        lines = _run(out, SECTIONS[view])
        return lines if any(line.strip() for line in lines) else ["", "nothing to show under %s" % view]
    return _run(out, [block for blocks in SECTIONS.values() for block in blocks])
