"""The log line for founder-hours given back while the household is in arrears."""
from typing import List, Tuple

from sim.refusal import LogLine
from .units_prose import plain_number


def arrears_hours_line(lost: List[Tuple[str, float]]) -> LogLine:
    """One line naming each project and the hours it lost; `lost` pairs a project id with its hours."""
    total = sum(hours for _, hours in lost)
    names = ", ".join("%s (%s hr)" % (node_id, plain_number(hours)) for node_id, hours in lost)
    return LogLine(
        "arrears_hours_lost", "IN ARREARS: %s founder-hours meant for %s did "
        "almost nothing this year, on top of the money "
        "- that time does not come back, arrears or not. "
        "'work' sells idle hours for wages instead of "
        "losing them here; clearing the arrears is what "
        "stops it happening again" % (plain_number(total), names),
        hours=total, projects=[node_id for node_id, _hours in lost])
