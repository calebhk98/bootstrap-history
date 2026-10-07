# Sellers may only cut their asks, so prices ratchet down and durable purchases swing

**Status:** open - known failing test: `economy_service_lives` ("it is not bought again in full")

The seller-pricing rule built for Complaint 336 (`sim/economy/seller_pricing.py`, `seller_offers.py`, hooked into `year_goods.py`) lets a producer that moves the clearing price cut its ask against the market's book, but never raise it (a labelled heuristic standing in for many workshops that cannot hold goods back together). With cuts only, a durable good's price drifts down year after year. In the service-lives fixture, households keep buying well above wear long after their stock is filled, and the stock swings up and down from year to year instead of settling. Before the pricing hook, purchases fell to about the wear once the stock was full.

Evidence: `python3 -m sim.tests --only economy_service_lives` fails "it is not bought again in full": late purchases exceed the bound of a small multiple of late wear. Print the path with `python3 -c "from sim.tests import test_economy_service_lives as t; [print(year, [round(value, 1) for value in row[:3]]) for year, row in enumerate(t.years_of(t.durable_setup(), 13))]"`; running the same at the commit before the pricing merge (`git log --merges --grep profit-seeking-seller-pricing`) shows the settled path.

What it would take: the restraint half of the pricing build in `Complaints/reports/innovator-pricing-research.md`: a seller with market power may also raise its ask (or withhold) when that earns more, and capacity is judged at the price expected after the seller's own additions. The two-year cobweb swing the pricing agent reported in the coffee scenario is likely the same cause. Do not loosen the test's bound; it is catching the instability.

Related: 336.
