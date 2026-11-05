"""The home country's output and coin stock come from the economy's own country figures like a partner's; the engine's
own formulas answer only while the economy is not open (and a fiat standard has no metal to count)."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.markets import port_money
from sim.markets.agent_views_outcome import AgentOutcomeViews


def _world(coin, stock=2000.0, price=0.5):
    return SimpleNamespace(
        scenario=SimpleNamespace(civ={"coin_standard": coin}, output_factor=0.5),
        goods_market=SimpleNamespace(offers=SimpleNamespace(home_unit_price=lambda material: price)),
        finance=SimpleNamespace(coin_stock_units=lambda: stock, real_output_hours=lambda: 40.0),
        labour=SimpleNamespace(money_per_labour_hour=lambda: 3.0))


class _Answers:
    def society_output(self):
        return 77.0

    def coin_stock_value(self):
        return 55.0


class _NoRecord:
    def society_output(self):
        return None

    def coin_stock_value(self):
        return None


world = _world({"material": "silver", "kg_per_unit": 0.01})
check("with the economy open, home output is the economy's country answer",
      port_money.output_value_of(_Answers(), world) == 77.0)
check("...and home coin stock likewise", port_money.coin_stock_value_of(_Answers(), world) == 55.0)
check("while the economy is not open, output is the engine's own figure",
      port_money.output_value_of(None, world) == 60.0)
check("while the economy is not open, coin stock is the engine's own figure",
      abs(port_money.coin_stock_value_of(None, world) - 2000.0 * 0.01 * 0.5) < 1e-12)
check("an open economy with no producers on the tiles keeps the engine figure",
      port_money.output_value_of(_NoRecord(), world) == 60.0)
check("an open economy whose money has no price answers None, not the engine's metal count",
      port_money.coin_stock_value_of(_NoRecord(), world) is None)

fiat = _world({"kg_per_unit": 0.0})
check("a fiat standard (no material) counts no metal: None, no KeyError",
      port_money.coin_stock_value_of(None, fiat) is None)


# --- the outcome views open the economy through the port, or answer None while it opens
class _Economy:
    def __init__(self):
        self.built = 0
        self.agent = SimpleNamespace(economy=self._build)

    def _build(self):
        self.built += 1
        raise AssertionError("a view built the economy outside open_agent")

    def answering(self):
        return None


def _views(economy):
    views = object.__new__(AgentOutcomeViews)
    views.parts = SimpleNamespace(market_objects=SimpleNamespace(economy=economy))
    return views


opening = _Economy()
views = _views(opening)
check("agent_health is None while the economy opens", views.agent_health() is None)
check("agent_opening_figures is None while the economy opens", views.agent_opening_figures() is None)
check("agent_stale_goods is None while the economy opens", views.agent_stale_goods() is None)
check("agent_traded_staple is None while the economy opens", views.agent_traded_staple() is None)
check("agent_opening_setup is None while the economy opens", views.agent_opening_setup() is None)
check("none of them built the economy", opening.built == 0)
