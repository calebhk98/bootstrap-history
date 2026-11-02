"""The acting seat's farm holding: the land it holds and the area cleared. Agriculture buys and sells the land, the farm
workforce sets the cleared area, and thieves take grain, each by a command. Food eaten, harvest and grain stock are the
agent economy's."""


class Farm:

    def farm_holdings(self):
        """The acting seat's farm: hectares held (None before a farm), the granary in kilograms and the area cleared (None
        before the farm workforce sets it)."""
        seat = self.seat
        return {"hectares": seat.farm_hectares, "stock_kg": seat.farm_stock_kg, "cleared_hectares": seat.farm_cleared_hectares}

    def change_farmland(self, command):
        seat = self.seat
        seat.farm_hectares = (seat.farm_hectares or 0.0) + command.hectares
        return seat.farm_hectares

    def set_cleared_farmland(self, command):
        self.seat.farm_cleared_hectares = command.hectares

    def take_from_granary(self, command):
        self.seat.farm_stock_kg = max(0.0, self.seat.farm_stock_kg - command.kilograms)
