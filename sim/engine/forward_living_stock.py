"""One-line forwarders from `Sim` to the living-stock and defence-stores modules, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.living_stock.api import ChangeHeld

from .blockers import blocker_kind


@blocker_kind("supply")
def check_unheld_stock(self, node_id, node, ignore_trade, _memo, _why):
    """Refuse a node whose `holds` the actor does not hold; the refusal names what is short."""
    short = self.stock_missing(node_id)
    if not short:
        return None
    if not _why:
        return False, None
    return False, ("it needs living stock you do not hold: %s. Get it by trade, gift or "
                   "expedition; it is not something you can research"
                   % ", ".join("%s (%.3g more)" % pair for pair in short))


class ForwardLivingStockMixin:

    def stock_held(self, material):
        return self.view("stock_held")[material]

    def stock_missing(self, node_id):
        return self.view("stock_status")[node_id]["missing"]

    def stock_gates(self, node_id):
        return self.view("stock_status")[node_id]["gates"]

    def stock_needed_by(self, node_id):
        return self.view("stock_status")[node_id]["needed_by"]

    def stock_holds_met(self, holds):
        return self.view("stock_holds_met")(holds)

    def held_living_stock(self):
        return self.view("held_living_stock")()

    def grant_stock(self, material, units):
        self.send(ChangeHeld(material, units))

    def change_stock(self, material, units):
        self.send(ChangeHeld(material, units))

    def venture_garrison(self, node_id, units=1.0):
        return self.view("venture_garrison")(node_id, units)

    def counter_supply_gap(self, node_id, kind, label):
        return self.view("counter_supply_gap")(node_id, kind, label)

    def relief_kcal_per_day(self):
        return self.view("relief_kcal_per_day")()
