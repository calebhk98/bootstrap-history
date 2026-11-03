"""Complaint 473: the mint buys bullion at the mint price (parity less the charge) from whoever sells it, not at the sellers'
own asks. `mint_price.top_ups` is called with the mint price and a clearing; it returns what the mint adds for each seller
it bought from, so that its purchase costs the mint price."""

QUICK_TOPIC = True

from .harness import check

from sim.economy.mint_price import melting_pays, received_price, top_ups
from sim.economy.types import ClearingResult, Fill, Pairing


def clearing(sells, mint_takes, price=80.0, paired=True):
    """A clearing of `sells` (agent, tile, quantity, ask) in which the mint took `mint_takes` (quantity per seller)."""
    fills = [Fill(agent, "metal", "town", tile, quantity, ask, "sell") for agent, tile, quantity, ask in sells]
    bought = sum(mint_takes)
    fills.append(Fill("edge:mint", "metal", "town", "t0", bought, price, "buy"))
    pairing = Pairing((("edge:mint", "t0"),), tuple((agent, tile) for agent, tile, _quantity, _ask in sells),
                      tuple(ask for _agent, _tile, _quantity, ask in sells), (0,) * len(sells), tuple(range(len(sells))),
                      tuple(mint_takes)) if paired else None
    return ClearingResult("metal", "town", "coin", price, bought, bought, 800.0, tuple(fills), pairing=pairing)


SELLS = [("mine_a", "t1", 600.0, 80.0), ("mine_b", "t2", 200.0, 90.0)]
paired = clearing(SELLS, [60.0, 40.0])

added = top_ups(95.0, paired)
check("each seller is topped up from its own ask to the mint price on what the mint took from it",
      added == {"mine_a": 60.0 * 15.0, "mine_b": 40.0 * 5.0}, added)
check("a seller that asked the mint price or more is not topped up",
      top_ups(85.0, paired) == {"mine_a": 60.0 * 5.0}, top_ups(85.0, paired))
check("nothing bought adds nothing", top_ups(95.0, clearing(SELLS, [0.0, 0.0])) == {})
check("no sellers add nothing", top_ups(95.0, clearing([], [])) == {})
check("the book's own edges are not paid a top-up",
      top_ups(95.0, clearing([("edge:mint", "t1", 5.0, 100.0)] + SELLS[:1], [5.0, 10.0])).keys() == {"mine_a"})
# settlement follows the clearing's pairing: a result that traded carries one, so a clearing without one has no taking to top up
unpaired = clearing(SELLS, [60.0, 40.0], paired=False)
check("a clearing with no pairing has no taking by the mint to top up, however much the mint bought",
      top_ups(95.0, unpaired) == {} and received_price(95.0, unpaired) == 80.0, (top_ups(95.0, unpaired), received_price(95.0, unpaired)))

check("the mint holds its coin metal while bullion is cheaper than coin", not melting_pays(88.0, 100.0))
check("the mint sells coin metal once bullion fetches at least parity", melting_pays(100.0, 100.0))
check("the mint holds its coin metal with no price remembered", not melting_pays(None, 100.0))

# what a seller of the metal is paid per unit, top-up included: the price makers plan with
check("the price received per unit sold is the market price plus the top-ups spread over the sellers' sales",
      abs(received_price(95.0, paired) - (80.0 + (60.0 * 15.0 + 40.0 * 5.0) / 800.0)) < 1e-9, received_price(95.0, paired))
check("with nothing bought the received price is the market price", received_price(95.0, clearing(SELLS, [0.0, 0.0])) == 80.0)
check("a market price above the mint price is the received price", received_price(70.0, paired) == 80.0)
check("with no sellers the received price is the market price", received_price(95.0, clearing([], [])) == 80.0)

# the mint tops up only what the settlement delivered to it
short = top_ups(95.0, paired, {("mine_a", "t1"): 20.0, ("mine_b", "t2"): 40.0})
check("a seller short of stock is topped up only on the units it delivered",
      short == {"mine_a": 20.0 * 15.0, "mine_b": 40.0 * 5.0}, short)
check("a seller that delivered nothing is not topped up", top_ups(95.0, paired, {}) == {})
