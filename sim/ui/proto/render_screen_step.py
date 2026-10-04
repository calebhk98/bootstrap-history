"""The step screen: the state screen with alerts and problems stitched on."""

from .render_screen_state import render_state
from .step_problems import problems_lines
from .step_alerts import alert_lines


def render_step(out):
    # step()'s reply is completed/events stitched onto a full state() reply;
    # render_state already knows how to read completed/events off the front.
    rendered = render_state(out)
    alerts = alert_lines(out.get("alerts"))
    if alerts:
        rendered = "\n".join(alerts) + "\n\n" + rendered
    problems = problems_lines(out.get("problems"))
    return rendered + "\n" + "\n".join(problems) if problems else rendered
