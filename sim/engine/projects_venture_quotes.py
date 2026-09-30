"""What a concern really earns and costs, and what reopening it costs: one figure for every screen."""


class VentureQuotesMixin:

    def venture_real_earnings(self, node_id, units=1.0, fully_ramped=False):
        """Yearly takings as the ledger credits them, the figure `ventures` prints.

        Applies the economy, output factor and price level the tree's raw
        revenue lacks, and, for a running concern, its revenue ramp and its
        goods market. `fully_ramped` leaves the ramp out (what it reaches).
        """
        running = node_id in self.state.projects.operating
        ramp = 1.0 if fully_ramped or not running else self.venture_ramp(node_id)
        market = self.goods_market_factor(node_id) if running else 1.0
        return self.concern_takings(node_id, ramp) * units * market

    def venture_real_upkeep(self, node_id, units=None):
        """Yearly running cost at the current price level: the figure every
        screen quotes and the ledger charges (`upkeep`). `units` prices a
        stated number of units of the concern instead of what is open now."""
        if units is None:
            return self.institution_upkeep(node_id) * self.price_index
        return self.nodes[node_id]["up"] * units * self.price_index

    def reopen_units(self, node_id):
        """How much of a scalable institution a reopening restores (one, for anything else)."""
        if node_id not in self.SCALABLE_INSTITUTIONS:
            return 1.0
        return getattr(self.household, "inst_units", {}).get(node_id, 1.0)

    def reopen_fee(self, node_id, unit_count=1.0):
        """What bringing a shut concern back costs, for `open` and `restore` alike.

        A concern the staffing rule shut within STAFF_CLOSURE_GRACE keeps its
        premises, so it costs a fraction; any other shut concern costs the
        ordinary opening fee. A work that is not a concern costs a share of
        building it again, never less than some years of its upkeep.
        """
        if self.is_venture(node_id):
            fee = self.venture_capex(node_id) * unit_count
        else:
            fee = max(self.project_cost(node_id) * self.RESTORE_COST_SHARE_OF_BUILD,
                      self.nodes[node_id]["up"] * self.RESTORE_COST_MIN_UPKEEP_YEARS)
        age = self.staff_closure_age(node_id)
        if age is not None and age <= self.STAFF_CLOSURE_GRACE:
            fee *= self.STAFF_CLOSURE_DISCOUNT
        return fee
