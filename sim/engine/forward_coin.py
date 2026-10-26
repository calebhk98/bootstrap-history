"""One-line forwarders from `Sim` to the coin module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) itself."""


class ForwardCoinMixin:

    def home_coin_metal(self):
        return self.view("home_coin_metal")()

    def home_price_level(self):
        return self.view("home_price_level")()

    def partner_price_level(self, civilization_id):
        return self.view("partner_price_level")[civilization_id]

    def home_coin_stock_units(self):
        return self.view("home_coin_stock")()

    def _partner_coin_opening_units(self, civilization_id):
        return self.view("partner_coin_opening")[civilization_id]

    def coin_carriage_units(self, civilization_id, units, home_money_per_partner_coin):
        return self.view("coin_carriage_units")(civilization_id, units, home_money_per_partner_coin)

    def coin_hoard_report(self):
        return self.view("coin_hoard_report")()
