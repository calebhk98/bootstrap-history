"""Complaint 370: a good offered after the opening becomes household demand once it is priced, and is valued at the price it was
introduced at. `new_goods_units` and `prices_in_hours` are called on built inputs; `_close_real_output` on a stand-in game."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.engine.household_new_goods import new_goods_units, prices_in_hours
from sim.engine.real_output import RealOutputMixin

OPENING = {"grain": 100.0, "cloth": 20.0}

# ---- priced goods
priced = prices_in_hours({"grain": 4.0, "cement": 12.0, "pearl": 0.0, "silk": 30.0}, 2.0, {"grain": 3.0}, {"cement": True, "silk": False})
check("a good the opening held is priced in labour hours", priced["grain"] == 2.0, priced)
check("a good the home society now offers is priced in labour hours", priced["cement"] == 6.0, priced)
check("a good only a partner offers is not the home market's", "silk" not in priced, priced)
check("a good with no positive price is left out", "pearl" not in priced, priced)

# ---- new goods
wanted = {"grain": 120.0, "cement": 5.0, "silk": 2.0, "tile": 3.0, "dud": 0.0}
units = new_goods_units(wanted, OPENING, {"grain": 2.0, "cement": 6.0, "dud": 1.0})
check("a good nothing offers at the opening draws demand once it is priced", units == {"cement": 5.0}, units)
check("a good that is not priced draws none", "silk" not in units and "tile" not in units, units)
check("a good the opening held is not a new good", "grain" not in units, units)
check("a good wanted in no quantity is not listed", "dud" not in units, units)
check("with nothing priced nothing is wanted", new_goods_units(wanted, OPENING, {}) == {}, None)
check("the new goods are listed in sorted order", list(new_goods_units({"b": 1.0, "a": 1.0}, {}, {"a": 1.0, "b": 1.0})) == ["a", "b"], None)

# ---- the introduction price
def closing_game(price, introduction):
    game = SimpleNamespace(
        labour=SimpleNamespace(money_per_labour_hour=lambda: 2.0), goods_market=SimpleNamespace(household_prices=lambda: {"cement": price}),
        household_new_goods_units=lambda: {"cement": 5.0}, state=SimpleNamespace(economy=SimpleNamespace(
            introduction_prices=introduction, output_per_head=1.0)), population=SimpleNamespace(total=1.0),
        _opening_population=lambda: 1.0, traded_measure=lambda: ({}, 1.0), opening_output_hours=lambda measure: 1.0,
        real_output_hours=lambda measure: 1.0)
    return game


introduction = {}
RealOutputMixin._close_real_output(closing_game(12.0, introduction))
check("the first close values a new good at its price in labour hours", introduction == {"cement": 6.0}, introduction)
RealOutputMixin._close_real_output(closing_game(30.0, introduction))
check("a later close leaves its introduction price where it was", introduction == {"cement": 6.0}, introduction)
