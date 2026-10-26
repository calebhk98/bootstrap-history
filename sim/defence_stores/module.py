"""What a standing work holds in hand and hands out: a magazine and a garrison for a defence, grain for the nation.

A `hazard_counters` entry may name a `magazine` ({material: units}, held in the stock ledger) and `draws` ({material:
units} spent in each year a threat it answers is live). A node may name a `garrison` ({trade: people}) drawn from the
labour market; an open concern holds its garrison the way it holds a foreman. A node's `banks_output` ({material,
per_labour_hour}) makes a running work put that material into the ledger from its crew's hours. A counter counts for the
share of its magazine held and of its garrison present, and says which fell short. A work that declares
`mechanics.food_relief` hands out the material it consumes, which the nation's people eat on top of the harvest. Nothing
here names a node or a material."""
from sim.assembly.api import Module
from sim.living_stock.api import ChangeHeld
from sim.unit_conversions import CIVIL_DAYS_PER_YEAR

from . import rules


class DefenceStores(Module):

    def venture_garrison(self, node_id, units=1.0):
        return rules.venture_garrison(self.needs.tree[node_id].get("garrison"), units)

    def garrison_claims(self):
        """{trade: people} claimed by every built garrison in force: a concern when open, a work with no doors to
        shut always."""
        operating = self.needs.operating()
        claims = {}
        for node_id in sorted(self.needs.techniques_done()):
            node = self.needs.tree[node_id]
            if not node or not node.get("garrison"):
                continue
            if self.needs.is_venture[node_id] and node_id not in operating:
                continue
            for trade, people in self.venture_garrison(node_id).items():
                claims[trade] = claims.get(trade, 0.0) + people
        return claims

    def garrison_share(self, node_id):
        needed = self.venture_garrison(node_id)
        if not needed:
            return 1.0, None
        return rules.garrison_share(needed, self.garrison_claims(), self.needs.staff()["employees"])

    def magazine_share(self, counter):
        return rules.magazine_share(counter.get("magazine"), lambda material: self.needs.stock_held[material])

    def counter_supply_gap(self, node_id, kind, label):
        """(share in force, words for what is short or None) of a counter's magazine and garrison."""
        magazine, material = self.magazine_share(rules.counter_spec(self.needs.tree[node_id], kind, label))
        garrison, trade = self.garrison_share(node_id)
        return rules.supply_gap(magazine, material, garrison, trade)

    def draw_defence_stores(self, year):
        """Spend each built counter's `draws` from the ledger in a year a threat of its kind is live."""
        live = self.needs.live_hazard_kinds(year)
        for node_id in sorted(self.needs.techniques_done()):
            for counter in ((self.needs.tree[node_id].get("mechanics") or {}).get("hazard_counters") or ()):
                if counter["kind"] not in live:
                    continue
                for material, units in sorted((counter.get("draws") or {}).items()):
                    self.needs.send(ChangeHeld(material, -min(units, self.needs.stock_held[material])))

    def bank_works_output(self):
        """Put into the ledger what each running work that `banks_output` makes in a year from its crew's hours."""
        for node_id, spec in self.needs.running_mechanics("banks_output"):
            node = self.needs.tree[node_id]
            crew_hours = (node["sch"] + node["art"]) * self.needs.hours_per_person_year() * self.needs.institution_units[node_id]
            self.needs.send(ChangeHeld(spec["material"], crew_hours * spec["per_labour_hour"]))

    def step_defence_stores(self, seat_id):
        """The year's turn of the magazines: the threats of the year spend, then the works restock."""
        self.draw_defence_stores(self.needs.year())
        self.bank_works_output()

    def relief_kcal_per_day(self):
        """The food energy a day, over the whole nation, that open works hand out."""
        handouts = []
        for node_id, spec in self.needs.effects_in_force("food_relief"):
            kilograms = (self.needs.tree[node_id].get("annual_consumables") or {}).get(spec["material"], 0.0)
            handouts.append((kilograms * self.needs.institution_units[node_id], spec["energy_kcal_per_kg"]))
        return rules.relief_kcal_per_day(handouts, CIVIL_DAYS_PER_YEAR)
