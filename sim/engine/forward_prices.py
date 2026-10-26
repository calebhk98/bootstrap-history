"""One-line forwarders from `Sim` to the prices module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) itself."""
from sim.prices.api import rules, shared_ledger


class ForwardPricesMixin:

    def _material_prices(self):
        return self.view("material_prices")()

    def _price_tables(self):
        return self.view("price_tables")()

    def _material_price_per_kg(self, tag):
        return self.view("material_price")[tag]

    def _priced_key(self, tag, prices):
        return rules.priced_key(tag, prices, self.view("commodity_record")[tag])

    def material_price_basis(self, material):
        return self.view("material_price_basis")[material]

    def _commodity_ledger(self):
        return shared_ledger()

    def _material_commodity_map(self):
        return self.view("material_commodity_map")()

    def _done_memo(self, name, key, compute):
        return self.view("done_memo")(name, key, compute)

    def _producers_memo(self, name, key, compute):
        return self.view("producers_memo")(name, key, compute)

    def commodity_floor_ratio(self, commodity):
        return self.view("commodity_floor_ratio")[commodity]

    def founder_concern_offers(self, commodity):
        return self.view("concern_offers")(commodity)
