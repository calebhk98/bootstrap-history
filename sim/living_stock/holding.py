"""What the module answers about held stock: how much, what a node lacks, and how an opening is credited."""
from sim.labour.api import production_data
from sim.ledger.api import ChangeStock
from sim.world.material_units import tonnes_per_unit

from . import rules
from .data import kilograms_per_unit, stock_rates

HERDS = "herds"


class Holding:
    """Views over the held stock and the commands that change it (needs: goods_stock, material_commodity, tree,
    civilisation, stock_land, endemic_stock_loss, producer_capacities)."""

    def commodity_of(self, material):
        return self.needs.material_commodity[material]

    def held(self, material):
        """Units of `material` held now."""
        return rules.held_units(self.needs.goods_stock[self.commodity_of(material)], tonnes_per_unit(material))

    def held_tonnes_of(self, material):
        return self.needs.goods_stock[self.commodity_of(material)]

    def stock_held(self, material):
        return self.held(material)

    def held_living_stock(self):
        return rules.held_herds(self.held, stock_rates())

    def stock_status(self, node_id):
        """{missing: [(material, units short)], gates: [...], needed_by: [...]} of one node's living-stock needs."""
        node = self.needs.tree[node_id]
        holds = node.get("holds")
        gates = rules.stock_gates(holds, self.needs.civilisation().get("needs_first"), node_id, self.held)
        return {"missing": rules.missing_stock(holds, self.held_tonnes_of, tonnes_per_unit),
                "gates": gates, "needed_by": rules.needed_by(gates)}

    def stock_holds_met(self, holds):
        """Whether every {material: units} in `holds` is held."""
        return not rules.missing_stock(holds, self.held_tonnes_of, tonnes_per_unit)

    def society_herds(self):
        return self.world.society_herds

    # ---- changing what is held ----

    def change_held(self, command):
        """Add (or, negative, take away) units of a held material: the ledger entries a grant writes."""
        self.change(command.material, command.units)

    def change(self, material, units):
        # Complaint 681, kept until the migration's last equivalence proof: the old living-stock path took the
        # opening snapshot after the change
        self.needs.send(ChangeStock(self.commodity_of(material), float(units) * tonnes_per_unit(material),
                                    legacy_snapshot_after_change=True))

    def grant_opening_stock(self, command=None):
        """Credit what the civilisation held at its date."""
        for material, units in sorted((self.needs.civilisation().get("opening_stock") or {}).items()):
            if not material.startswith("_"):
                self.change(material, units)

    def opening_herd_units(self):
        """{stock material: units} the herd producers keep, before the pasture holds it down."""
        return rules.herd_units_kept(self.needs.producer_capacities(), production_data())

    def endemic_keeping(self, material):
        rates = stock_rates().get(material) or {}
        loss = self.needs.endemic_stock_loss(self.needs.stock_land()["place"], rates.get("species"))
        return rules.endemic_keeping(rates, loss)

    def grant_opening_herds(self, command=None):
        """Credit the opening herds to the ledger, scaled down together if the held tiles' pasture cannot carry them."""
        herds = rules.opening_herds(self.opening_herd_units(), self.needs.stock_land()["pasture_kg"],
                                    kilograms_per_unit, self.endemic_keeping)
        for material, units in herds.items():
            self.change(material, units)
            self.world.society_herds[material] = units
        self.bump(HERDS)
