"""What a failed action takes of what it risked: its crew, its hull and its cargo.

A node's `risks` is {"crew": {trade: share}, "hull": {material: share}, "cargo": {material: share}}.
Crew is taken from the household's employees person by person; hull and cargo are taken from the held
stock, so a failed voyage leaves the owner with less than it sailed with. Nothing here names a node.
"""

STOCK_RISKS = ("hull", "cargo")


class ActionLossMixin:

    def lose_what_was_risked(self, node_id):
        """Take the crew, hull and cargo a failed attempt put at risk. Returns the log lines saying what went."""
        risks = self.nodes[node_id].get("risks")
        if not risks:
            return []
        lines = []
        employees = self.state.household.employees
        for trade, share in sorted((risks.get("crew") or {}).items()):
            have = employees.get(trade, 0.0)
            kept = self._surviving_people(have, 1.0 - share)
            if kept > 0:
                employees[trade] = kept
            else:
                employees.pop(trade, None)
            if round(have) - kept > 0:
                lines.append("crew lost: %d of %d %s" % (round(have) - kept, round(have), trade))
        for kind in STOCK_RISKS:
            for material, share in sorted((risks.get(kind) or {}).items()):
                lost = self.stock_held(material) * share
                if lost > 0:
                    self.change_stock(material, -lost)
                    lines.append("%s lost: %.3g of %s" % (kind, lost, material))
        return lines
