"""What worker housing and a trade-school seat cost now, and building housing.

Prices are a labour-hour figure scaled by the price level; the figures belong with the workforce and finance topics
(the workforce module reads them as `housing_price_per_place` and `trade_school_price_per_seat`)."""
from sim.constants import declare
from . import money_units
from sim.agents.api import edges


class HousingPriceMixin:

    HOUSING_LABOUR_HOURS_PER_PLACE = declare(
        "HOUSING_LABOUR_HOURS_PER_PLACE", 12000.0, kind="temporary_heuristic",
        unit="labour hours per place", source=None, confidence="D",
        why="Cost to build one place of durable worker housing. Not "
            "sourced to any attested construction cost; an invented figure "
            "sized to make the lever meaningful without being free.")
    HOUSING_COST_PER_PLACE = money_units.PricedInLabourHours("HOUSING_LABOUR_HOURS_PER_PLACE")
    TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT = declare(
        "TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT", 24000.0, kind="temporary_heuristic",
        unit="labour hours per seat", source=None, confidence="D",
        why="Cost to found one seat of a named trade school (see "
            "labour.py's consumer of this figure, outside this file's "
            "scope). Not sourced to any attested cost of pre-industrial "
            "vocational training.")
    TRADE_SCHOOL_COST_PER_SEAT = money_units.PricedInLabourHours("TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT")

    def trade_school_price_per_seat(self):
        """What one trade-school seat costs now (`buy school`, `quote school`)."""
        return self.TRADE_SCHOOL_COST_PER_SEAT * self.price_index

    def housing_price_per_place(self):
        """What one place of worker housing costs now (`buy housing`, `quote housing`, room advice)."""
        return self.HOUSING_COST_PER_PLACE * self.price_index

