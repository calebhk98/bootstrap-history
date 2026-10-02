"""Where the market ceiling's deduction falls.

Revenue passes through one saturating ceiling after the concerns are added up,
so every earner is cut by the same share. The ledger states the total cut; this
attributes it to the categories (and the workshop) that suffer it, so the rows
sum to that total.
"""

WORKSHOP_CATEGORY = "your own workshop"
CONCERNS_NAMED_PER_CATEGORY = 6


class MarketAbsorptionMixin:

    def market_absorption_by_category(self, deduction):
        """Rows {category, nominal, absorbed, lost, concerns} whose `lost`
        values add up to `deduction`, the figure the ledger deducts."""
        if deduction <= 0:
            return []
        economy = self.state.economy
        rows = self.ledger_concern_rows()
        groups = {}
        for node_id, amount in rows.items():
            category = self.nodes[node_id].get("cat") or "other"
            group = groups.setdefault(category, {"nominal": 0.0, "members": []})
            group["nominal"] += amount
            group["members"].append((amount, node_id))
        workshop = self.workshop_output() * economy.output_factor
        if workshop > 0.5:
            groups[WORKSHOP_CATEGORY] = {"nominal": workshop, "members": []}
        squeezed_total = sum(group["nominal"] for group in groups.values())
        if squeezed_total <= 0:
            return []
        out = []
        for category, group in groups.items():
            lost = round(deduction * group["nominal"] / squeezed_total, 1)
            members = sorted(group["members"], key=lambda member: (-member[0], member[1]))
            out.append({"category": category, "nominal": round(group["nominal"], 1),
                        "lost": lost,
                        "concerns": [node_id for _amount, node_id
                                     in members[:CONCERNS_NAMED_PER_CATEGORY]]})
        out.sort(key=lambda row: (-row["lost"], row["category"]))
        # Rounding residue goes to the largest row, so the rows sum exactly.
        residue = round(deduction - sum(row["lost"] for row in out), 1)
        out[0]["lost"] = round(out[0]["lost"] + residue, 1)
        for row in out:
            row["absorbed"] = round(row["nominal"] - row["lost"], 1)
        return out
