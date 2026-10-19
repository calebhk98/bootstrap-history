"""Scans the concerns a game's society holds for whether they pay their way (sim/agents/concern_scan.py)."""
from typing import Any, Dict, List

from sim.agents.api import concern_scan

from .agents_port import SimWorld


def held_concerns(game) -> List[str]:
    """Nodes the society holds that describe a going concern (they earn or cost to keep up)."""
    return sorted(node_id for node_id in game.done if game.is_concern_node(node_id))


def scan_game(game) -> Dict[str, Any]:
    """The summary (concern_scan.summary) of the concerns `game`'s society holds, at its current prices."""
    rows = concern_scan.scan(game.actors, SimWorld(game), held_concerns(game))
    return concern_scan.summary(rows)


def lines(civ_id: str, summary: Dict[str, Any]) -> List[str]:
    """The scan as plain lines: the count that pay, then the payers and the biggest losers with their figures."""
    share = "n/a" if summary["share"] is None else "%.3g" % summary["share"]
    out = ["%-16s concerns paying: %d of %d (share %s)" % (civ_id, summary["paying"], summary["count"], share)]
    for label, rows in (("pays", summary["pay"]), ("loses", summary["losers"])):
        for row in rows:
            out.append("%-16s   %-5s %-28s takings %12.4g  costs %12.4g (upkeep %.4g, wages %.4g, carried %.4g)" % (
                "", label, row["node"], row["takings"], row["costs"], row["upkeep"], row["wages"], row["carried"]))
    return out
