"""Complaint 473: the mint buys bullion at the mint price (parity less the charge) from whoever sells it, not at the sellers'
own asks. `mint_price.top_ups` is called with the quantity the mint bought, the price the market settled it at, the mint
price and the sellers' fills; it returns what the mint adds for each seller so the mint's purchase costs the mint price."""

QUICK_TOPIC = True

from .harness import check

from sim.economy.mint_price import melting_pays, top_ups
from sim.economy.types import Fill

sells = [Fill("mine_a", "metal", "town", "t1", 600.0, 80.0, "sell"), Fill("mine_b", "metal", "town", "t2", 200.0, 90.0, "sell")]

added = top_ups(100.0, 80.0, 95.0, sells)
check("the mint adds the gap between its price and the settled price on what it bought, shared by sales",
      abs(sum(added.values()) - 100.0 * 15.0) < 1e-9, added)
check("sellers share the top-up in proportion to what they sold",
      abs(added["mine_a"] - 3.0 * added["mine_b"]) < 1e-9, added)

check("a settled price above the mint price adds nothing", top_ups(100.0, 96.0, 95.0, sells) == {})
check("nothing bought adds nothing", top_ups(0.0, 80.0, 95.0, sells) == {})
check("no sellers add nothing", top_ups(100.0, 80.0, 95.0, []) == {})
check("the book's own edges are not paid a top-up",
      top_ups(10.0, 80.0, 95.0, [Fill("edge:mint", "metal", "town", "t1", 5.0, 100.0, "sell")] + sells[:1]).keys() == {"mine_a"})

check("the mint holds its coin metal while bullion is cheaper than coin", not melting_pays(88.0, 100.0))
check("the mint sells coin metal once bullion fetches at least parity", melting_pays(100.0, 100.0))
check("the mint holds its coin metal with no price remembered", not melting_pays(None, 100.0))
