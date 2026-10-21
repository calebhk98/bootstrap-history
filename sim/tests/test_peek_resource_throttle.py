"""A screen's question about a material throttle does not change the game: `_peek_throttle` hands back the answer and
puts back the stock, the draws, the shortage count and the memos the question touched. Called on a stub that holds what it
reads; the same question asked of a running game is in test_peek_resource_throttle_scenario."""
import collections
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.economy_electricity import ElectricityMixin

QUICK_TOPIC = True


def asked_game():
    stock = {"iron": 5.0}
    flows = {"draws": 1}
    holdings = SimpleNamespace(throttle=1.0, binding=None, shortages=collections.Counter({"coal": 2}),
                               _material_stock_opening={"iron": 5.0})
    household = SimpleNamespace(_stock_throttle_sig=("sig",), _stock_throttle_cache=(1.0, None), _material_demand_cache={"a": 1})
    market = SimpleNamespace(snapshot_flows=lambda: dict(flows), restore_flows=lambda saved: flows.update(saved) or
                             [flows.pop(key) for key in list(flows) if key not in saved])
    return SimpleNamespace(state=SimpleNamespace(holdings=holdings), household=household, goods_market=market,
                           _material_stock=lambda: stock), stock, flows


def throttling(game, stock, flows):
    """What a real throttle call does to the state it works on."""
    def compute():
        stock["iron"] = 0.0
        flows["draws"] = 9
        game.state.holdings.throttle, game.state.holdings.binding = 0.4, "iron"
        game.state.holdings.shortages["iron"] += 1
        game.state.holdings._material_stock_opening["iron"] = 0.0
        game.household._stock_throttle_sig = ("changed",)
        game.household._stock_throttle_cache = (0.4, "iron")
        game.household._material_demand_cache = None
        return 0.4
    return compute


game, stock, flows = asked_game()
factor, binding = ElectricityMixin._peek_throttle(game, throttling(game, stock, flows))
check("the peek answers what the throttle is and which pool binds it", (factor, binding) == (0.4, "iron"), (factor, binding))
check("the stock the question banked is put back", stock == {"iron": 5.0}, stock)
check("the draws it noted are put back", flows == {"draws": 1}, flows)
check("the throttle and binding the holdings carried are put back",
      (game.state.holdings.throttle, game.state.holdings.binding) == (1.0, None),
      (game.state.holdings.throttle, game.state.holdings.binding))
check("the shortage it counted is put back", game.state.holdings.shortages == collections.Counter({"coal": 2}),
      game.state.holdings.shortages)
check("the opening stock it recorded is put back", game.state.holdings._material_stock_opening == {"iron": 5.0},
      game.state.holdings._material_stock_opening)
check("the memos of the last real throttle are put back",
      (game.household._stock_throttle_sig, game.household._stock_throttle_cache, game.household._material_demand_cache)
      == (("sig",), (1.0, None), {"a": 1}), vars(game.household))
