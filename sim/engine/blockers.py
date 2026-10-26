"""The shared vocabulary of why a project cannot begin, and the mark a start check carries.

The classifier and the list of blockers are the projects module's (sim/projects/blocker_rules.py, blocker_views.py);
this file keeps the names the unmoved gates (living stock, materials, running gates, interest groups) import."""
from sim.projects.api import BLOCKER_KINDS, BLOCKER_MEANING, RUNNING_CONSTRAINT_KIND  # noqa: F401


def blocker_kind(kind):
    """Mark a start check with the kind of blocker it reports."""
    if kind not in BLOCKER_KINDS:
        raise ValueError("unknown blocker kind %r" % kind)

    def mark(check):
        check.blocker_kind = kind
        return check
    return mark
