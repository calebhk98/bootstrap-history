#!/usr/bin/env python3
"""Which goods' markets never clear, and why, per civilisation, over a run of the agent economy.

    python3 sim/economy_untraded.py --years 15 --seed 1
    python3 sim/economy_untraded.py --civs <civilisation>,<civilisation> --list

For every good with an opening price it reports whether the price ever left its opening value, whether
any year's market cleared, and for those that never did the reason, from the orders the market saw:
  no_recipe        no recipe in the data makes it and nobody ever bid or offered
  no_producer      a recipe makes it but no producer was ever set up
  not_ordered      producers exist but no order for it reached a market in any year
  buyers_only      bids but never an offer
  sellers_only     offers but never a bid
  ask_above_bids   both, and every seller's reservation was above every buyer's ceiling
  other            both, yet nothing cleared
shown_at_opening counts goods the game still shows at their opening price (stale: shown a cost or last
price, not a market's).
"""
import argparse
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)



def every_civilisation():
    from sim.engine import data
    return sorted(name[:-5] for name in os.listdir(data.CIVDIR) if name.endswith(".json") and not name.startswith("_"))
REASONS = ("no_recipe", "no_producer", "not_ordered", "buyers_only", "sellers_only", "ask_above_bids", "other")


class OrderLog:
    """What every market saw, by good: patched around goods_market.clear while a game runs."""

    def __init__(self):
        self.bids, self.offers, self.dry_ask_above, self.traded = {}, {}, {}, set()

    def watch(self, good, bids, offers, quantity):
        self.bids[good] = self.bids.get(good, 0) + len(bids)
        self.offers[good] = self.offers.get(good, 0) + len(offers)
        if quantity > 0.0:
            self.traded.add(good)
        elif bids and offers:
            ceilings = [bid.maximum_price for bid in bids if bid.budget > 0.0]
            asks = [offer.reservation_price for offer in offers]
            if ceilings and asks and min(asks) > max(ceilings):
                self.dry_ask_above[good] = True
            else:
                self.dry_ask_above.setdefault(good, False)


def reason(good, log, setup, record):
    if good in log.traded:
        return None
    made = any(good in setup.recipes[producer.recipe_id].outputs for producer in record.producers.values())
    if not log.bids.get(good) and not log.offers.get(good):
        if made:
            return "not_ordered"
        return "no_producer" if any(good in recipe.outputs for recipe in setup.recipes.values()) else "no_recipe"
    if not log.offers.get(good):
        return "buyers_only"
    if not log.bids.get(good):
        return "sellers_only"
    return "ask_above_bids" if log.dry_ask_above.get(good) else "other"


def measure(civ_id, seed, years):
    """(setup, record, log, frozen goods) after `years` yearly steps of a game on the agent economy."""
    from sim.economy import goods_market
    from sim.economy_validate import new_game
    log = OrderLog()
    original = goods_market.clear

    def watching(bids, offers, good, area, currency, last_price):
        result = original(bids, offers, good, area, currency, last_price)
        log.watch(good, bids, offers, result.quantity)
        return result

    goods_market.clear = watching
    try:
        game = new_game(civ_id, seed)
        for _year in range(years):
            if game.dead_reason:
                break
            game.step()
    finally:
        goods_market.clear = original
    economy = game.economy.agent.economy()
    return economy.setup, economy.record, log


def report(civ_id, seed, years, listing):
    setup, record, log = measure(civ_id, seed, years)
    goods = sorted(setup.opening_prices)
    nationals = {}
    for key, price in record.memory.prices.items():
        nationals.setdefault(key.split("|", 1)[0], []).append(price)
    frozen = [good for good in goods if good in nationals
              and all(math.isclose(price, setup.opening_prices[good], rel_tol=1e-12) for price in nationals[good])]
    reasons = {good: reason(good, log, setup, record) for good in goods}
    untraded = [good for good in goods if reasons[good]]
    counts = {name: sum(1 for good in untraded if reasons[good] == name) for name in REASONS}
    from sim.economy.notional import shown_prices
    shown, stale = shown_prices(setup, record)
    shown_frozen = [good for good in frozen if math.isclose(shown[good], setup.opening_prices[good], rel_tol=1e-12)]
    print("%-16s goods %3d  traded %3d  never_cleared %3d  frozen_at_opening %3d  shown_at_opening %3d  stale %3d  " % (
        civ_id, len(goods), len(goods) - len(untraded), len(untraded), len(frozen), len(shown_frozen), len(stale))
        + "  ".join("%s %d" % (name, count) for name, count in counts.items() if count))
    if listing:
        for good in untraded:
            print("    %-28s %-15s %s" % (good, reasons[good], "frozen" if good in frozen else "moved"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--years", type=int, default=15)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--civs", default="", help="comma-separated; every civilisation when empty")
    parser.add_argument("--list", action="store_true", help="name every good that never cleared")
    arguments = parser.parse_args(argv)
    for civ in [civ for civ in arguments.civs.split(",") if civ] or every_civilisation():
        report(civ, arguments.seed, arguments.years, arguments.list)
    return 0


if __name__ == "__main__":
    sys.exit(main())
