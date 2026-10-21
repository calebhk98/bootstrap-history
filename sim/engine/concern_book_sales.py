"""Which of the acting seat's concerns sell in the agent economy's book, and what they put in and take out of it.

A concern whose goods the economy trades is paid what the year's clearing pays for the units buyers took
(economy_port_year `_settle_seats`), like a firm's plant; the engine's estimate (`revenue`) covers only the rest.
The offer and the inputs bought are one rule here, read by the clearing, the estimate and the forecast alike."""
from . import concern_sales


class ConcernBookSalesMixin:

    def concern_book_scale(self, node_id):
        """The share of the concern's full-staffing year it runs now: its ramp, size and the hazard and war factor."""
        units = self.institution_units(node_id) if node_id in self.SCALABLE_INSTITUTIONS else 1.0
        return self.venture_ramp(node_id) * units * self.state.economy.output_factor

    def concern_book_offer(self, node_id):
        """{material: units} the concern puts in this year's clearing; empty for a concern the engine's estimate covers
        (not running as the acting seat's own, makes nothing from output, or nothing it makes is traded)."""
        projects = self.state.projects
        if node_id not in projects.operating or node_id in projects.granted or not self.is_venture(node_id):
            return {}
        baskets = self.concern_baskets_now(node_id)
        if baskets is None:
            return {}
        return concern_sales.offered_units(baskets.outputs, self.concern_book_scale(node_id), self.economy.agent_trades_good)

    def concern_sells_on_book(self, node_id):
        """Whether the clearing pays this concern, so the estimate leaves it out."""
        return bool(self.concern_book_offer(node_id))

    def concern_book_inputs_cost(self, node_id):
        """What the concern's year of inputs costs at the economy's prices, charged to the seat because the clearing
        pays the gross of its sales (the estimate was net of them); a price the economy lacks falls back to the
        long-run cost at today's price level."""
        baskets = self.concern_baskets_now(node_id)
        if baskets is None:
            return 0.0
        long_run = self._material_prices()

        def price_of(material):
            paid = self.goods_market.home_unit_price(material)
            if paid is not None:
                return paid
            cost = long_run.get(material)
            return None if cost is None else cost * self.price_index
        return concern_sales.inputs_cost(baskets.purchases, self.concern_book_scale(node_id), price_of)
