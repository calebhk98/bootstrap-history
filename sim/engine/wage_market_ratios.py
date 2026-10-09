"""The market ratios wages read: the staple's and the tools', as the last year's close left them.

A wage is set before the year's market clears (the clearing prices imports at a partner's landed price,
which needs a wage quote), so wages read the ratio recorded at the close, never the live clearing.
"""
from sim.labour import trade_data, wage_provider


class WageMarketRatiosMixin:

    def last_market_price_ratio(self, material):
        """The material's real price ratio at the last year's close; one before any close."""
        return self.state.economy.wage_market_ratios.get(material, 1.0)

    def record_wage_market_ratios(self):
        """Record the real price ratio of the staple and of every trade's tool materials."""
        registry = trade_data.registry_of(self)
        materials = {wage_provider.staple_material(self.civ)}
        for trade in registry:
            materials.update(trade_data.tool_basket(registry, trade))
        ratios = self.state.economy.wage_market_ratios
        for material in sorted(materials):
            ratio = self.real_price_ratio(material)
            ratios[material] = ratio if ratio and ratio > 0.0 else 1.0
