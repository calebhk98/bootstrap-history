"""The rest of the state screen (completed and events head, trailing notes) and render_state, the assembler of every state block."""

from .render_screen_state_views import render_view
from .util import _fmt_num, _wrap
from .wave_summary import summary_line
from .event_severity import event_marker, order_events


def _events_without_completion_repeats(completed, events):
    """The events minus each "completed: <name>" line that repeats a
    COMPLETED record, and the tail of that line ("STATUS: CLOSED ... Open
    it") keyed by name, to go on the single COMPLETED line instead."""
    tails = {}
    kept = []
    for event in events or []:
        message = event.get("message") or ""
        name = next((record.get("name") for record in completed or []
                     if record.get("name") and record.get("name") not in tails
                     and (message == "completed: " + record["name"]
                          or message.startswith("completed: %s. " % record["name"]))), None)
        if name is None:
            kept.append(event)
        else:
            after_name = message[len("completed: " + name):]
            tails[name] = after_name.replace(". ", " - ", 1)
    return kept, tails


def _state_completed_head_lines(out):
    """The loudest lines in the reply, built but not yet merged in front of
    the rest of the screen - split out of _state_completed_head so that
    function's own complexity is just the merge, not the four kinds of
    thing that can appear here.
    """
    completed = out.get("completed")
    events = out.get("events")
    lost = out.get("lost")
    fdts = out.get("the_founder_died_this_step")
    head = []
    if completed or events or lost or fdts:
        # THE LOUDEST LINE IN THE REPLY, not one more EVENT line among sixty.
        # See _founder_death_info and the step handler's own comment on why
        # a multi-year step stops here rather than running on past it.
        if fdts:
            head.append("  *** THE FOUNDER HAS DIED, aged about %s, in %s ***"
                        % (fdts.get("aged_about"), fdts.get("year")))
        headline = summary_line(out.get("summary"))
        if headline:
            head.append(headline)
        events, repeats = _events_without_completion_repeats(completed, events)
        for record in completed or []:
            head.append("  %s %s: %s%s"
                        % ("THIS SOCIETY NOW HAS" if record.get("granted")
                           else "COMPLETED", record.get("year"), record.get("name"),
                           repeats.get(record.get("name"), "")))
        for record in lost or []:
            head.append("  LOST %s: %s%s"
                        % (record.get("year"), record.get("name"),
                           " (restore brings it back for a fraction of the cost)"
                           if record.get("can_be_restored") else ""))
        for event in order_events(events):
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
            marker = event_marker(event.get("message"))
            head.append("  %sDURING %s: %s" % (marker + " " if marker else "",
                                                event.get("year"), event.get("message")))
            head.extend("      - " + detail for detail in event.get("details") or [])
        if out.get("stopped_early"):
            head.append("  " + out["stopped_early"])
    if out.get("victory"):
        head = _victory_lines(out["victory"]) + head
    return head


def _victory_lines(victory):
    lines = ["=" * 70, "VICTORY: %s, in %s AD, %s years after you arrived"
             % (victory.get("goal_in_words") or "the goal", victory.get("year"), victory.get("elapsed_years"))]
    if victory.get("points_so_far") is not None:
        lines.append("  score so far: %s of 1000" % victory["points_so_far"])
    if victory.get("achievements"):
        lines.append("  achievements: " + ", ".join(victory["achievements"]))
    lines.append(_wrap("  " + victory.get("to_see_your_score", ""), indent="  "))
    lines.append("=" * 70)
    return lines


def _state_completed_head(out, lines):
    """Not a section to append - the loudest lines in the reply, which go
    in FRONT of everything else. Takes the lines already built by the
    other sections and returns the merged list, exactly as the original
    inline `lines = head + [""] + lines if head else lines` did.
    """
    head = _state_completed_head_lines(out)
    lines = head + [""] + lines if head else lines
    return lines


def _state_also(out):
    lines = []
    also = out.get("also_available")
    if also:
        lines.append("")
        lines.append("more: " + "; ".join(also))
    return lines


def _render_sections(out, renderers):
    lines = []
    for renderer in renderers:
        lines += renderer(out)
    return lines


def render_state(out):
    """A position, not a dict: year, money, goal and what is about to happen to you first,
    then what is running and what each thing is waiting on, who you employ, where you stand.

    Works on both the short state() and state(full=true), and on step()'s
    reply, which is this same shape with completed/events stitched on front.
    A reply carrying `state_view` ("short", "full" or a section name) is
    rendered that way; one without it prints every section.
    """
    lines = render_view(out, out.get("state_view"))
    lines = _state_completed_head(out, lines)
    emergency = out.get("demographic_emergency")
    if emergency:
        lines = ["DEMOGRAPHIC EMERGENCY: population %+.0f%% in the last year" % (100 * emergency["population_change"]),
                 "  fewer people to farm, hire and pay taxes; expect wages and food prices to move", ""] + lines
    if out.get("state_view") in (None, "full"):
        lines += _state_also(out)
    return "\n".join(lines)
