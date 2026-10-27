"""Scans the plants of a game's society for whether they pay their way (sim/agents/concern_scan.py).

Two businesses are read: the plants the society could run, one of each concern it holds (a notional business, as an
entrant weighs them), and the plants every owner in the game runs now (the founder's seats and the actors')."""
from typing import Any, Dict, Iterator, List, Tuple

from sim.agents.api import Business, concern_scan

HELD_BUSINESS_ID = "held concerns"


def held_concerns(game) -> List[str]:
    """Nodes the society holds that describe a going concern (they earn or cost to keep up)."""
    return sorted(node_id for node_id in game.done if game.is_concern_node(node_id))


def held_business(game) -> Business:
    """One plant of each concern the society holds, as a business no one owns."""
    business = Business.running(held_concerns(game))
    business.business_id = business.owner_id = HELD_BUSINESS_ID
    return business


def running_businesses(game) -> Iterator[Tuple[str, Business]]:
    """(owner id, business) of every owner in the game: each seat's, then each actor's, in id order."""
    for seat_id in sorted(game.state.seats):
        yield seat_id, game.state.seats[seat_id].projects.business
    for actor_id in sorted(game.view("cast")().actors):
        yield actor_id, game.view("cast")().actors[actor_id].record.business


def scan_game(game) -> Dict[str, Any]:
    """The summary (concern_scan.summary) of the concerns `game`'s society holds, at its current prices, with the summary of
    the plants its owners run now under `running`."""
    world = game.view("actor_world")()
    result = concern_scan.summary(concern_scan.scan_business(held_business(game), game.view("cast")(), world))
    result["running"] = concern_scan.summary(concern_scan.scan_businesses(running_businesses(game), game.view("cast")(), world))
    return result


def lines(civ_id: str, summary: Dict[str, Any]) -> List[str]:
    """The scan as plain lines: the count that pay, then the payers and the biggest losers with their figures."""
    share = "n/a" if summary["share"] is None else "%.3g" % summary["share"]
    out = ["%-16s concerns paying: %d of %d (share %s); %d sell in the book" % (
        civ_id, summary["paying"], summary["count"], share, summary["selling"])]
    for label, rows in (("pays", summary["pay"]), ("loses", summary["losers"])):
        for row in rows:
            out.append("%-16s   %-5s %-28s takings %12.4g  costs %12.4g (upkeep %.4g, wages %.4g, carried %.4g)%s" % (
                "", label, row["node"], row["takings"], row["costs"], row["upkeep"], row["wages"], row["carried"],
                "" if row["sells"] else "  (sells nothing in the book)"))
    running = summary.get("running")
    if running is not None:
        out.append("%-16s plants running now: %d, of which %d pay" % ("", running["count"], running["paying"]))
    return out
