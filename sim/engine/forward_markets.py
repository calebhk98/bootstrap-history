"""One-line forwarders from the old `Sim` names of the markets topic to the markets module, for callers not yet in a module.

The goods market and the port over the agent economy are the markets module's (`economy`, `goods_market`); the screens, the port and the goods
market itself still say `sim._market_flows()`, `sim.market_state(...)` or `sim.buy_material_stock(...)`. Each line goes when its
last caller reads the view (`sim.view(name)`) or sends the command (`sim.send(command)`) itself."""
from sim.markets import categories


class ForwardMarketsMixin:

    # numbers other code still reads off the game
    GOODS_CATEGORIES = categories.GOODS_CATEGORIES
    ESSENTIAL_CATEGORIES = categories.ESSENTIAL_CATEGORIES

    # ---- the book and the year's flows ----

    # ---- the goods categories and what the screens read ----

    # ---- the founder at the market ----
