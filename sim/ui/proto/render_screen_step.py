"""The step screen: the state screen with alerts and problems stitched on."""

from .render_screen_state import render_state
from .step_problems import problems_lines
from .step_alerts import alert_lines
from .step_automation import automation_lines
from .render_programme import render_programme_rows

FULL_STATE_POINTER = 'Type "state full" for the full list.'


def render_step(out):
    # step()'s reply is completed/events stitched onto a short state() reply;
    # render_state already knows how to read completed/events off the front.
    rendered = render_state(out)
    alerts = alert_lines(out.get("alerts"))
    if alerts:
        rendered = "\n".join(alerts) + "\n\n" + rendered
    programme = render_programme_rows(out.get("programme") or [])
    if programme:
        programme = ["PROGRAMME:"] + ["  " + line for line in programme]
    trailing = automation_lines(out.get("automation")) + programme + problems_lines(out.get("problems"))
    if trailing:
        rendered = rendered + "\n" + "\n".join(trailing)
    return rendered + "\n\n" + FULL_STATE_POINTER
