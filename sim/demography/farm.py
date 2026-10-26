"""The acting seat's farm holding: the land it holds, its granary and what the last farm year left. The farm year itself is
`recovery.py`; agriculture buys and sells the land, the farm workforce sets the hours and the cleared area, and thieves take
grain, each by a command."""


class Farm:

    def farm_holdings(self):
        """The acting seat's farm: hectares held (None before a farm), the granary in kilograms, the area cleared (None before
        the farm workforce sets it), and what the last farm year closed with: the shortfall (None before the first), the gross
        harvest, the marginal product of the last hour of labour (None before the first), and the hours the farm needs (None
        before the farm workforce sizes it)."""
        seat = self.seat
        return {"hectares": seat.farm_hectares, "stock_kg": seat.farm_stock_kg, "cleared_hectares": seat.farm_cleared_hectares,
                "last_shortfall_kg": seat.farm_last_shortfall_kg, "last_harvest_kg": seat.farm_last_harvest_kg,
                "last_marginal_product": seat.farm_last_marginal_product, "hours_needed": seat.farm_hours_needed}

    def change_farmland(self, command):
        seat = self.seat
        seat.farm_hectares = (seat.farm_hectares or 0.0) + command.hectares
        return seat.farm_hectares

    def set_cleared_farmland(self, command):
        self.seat.farm_cleared_hectares = command.hectares

    def set_farm_hours_needed(self, command):
        self.seat.farm_hours_needed = command.hours

    def take_from_granary(self, command):
        self.seat.farm_stock_kg = max(0.0, self.seat.farm_stock_kg - command.kilograms)
