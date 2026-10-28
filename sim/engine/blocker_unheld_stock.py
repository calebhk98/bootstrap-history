"""The blocker that refuses a node whose living stock is not held."""
from .blockers import blocker_kind


@blocker_kind("supply")
def check_unheld_stock(self, node_id, node, ignore_trade, _memo, _why):
    """Refuse a node whose `holds` the actor does not hold; the refusal names what is short."""
    short = self.view("stock_status")[node_id]["missing"]
    if not short:
        return None
    if not _why:
        return False, None
    return False, ("it needs living stock you do not hold: %s. Get it by trade, gift or "
                   "expedition; it is not something you can research"
                   % ", ".join("%s (%.3g more)" % pair for pair in short))
