# Design: households hold part of their savings in durable stores of value (Complaint 404)

A design written by a research agent in economy round four. Labels: **[read]**, **[snippet]**,
**[memory]** (unverified). Steps 1-3 are being built; steps 4-7 wait for measurement.

## Why
- **Saving in plate.** Households above subsistence kept wealth in coin, loans, land and plate
  (jewellery, dowry metal, silverware). They bought it in good years and sold or pawned it in bad
  ones (Spufford; probate-inventory work [memory]).
- **Metal against bad coin.** Metal beat coin under debasement or inflation, and beat loans when the
  real rate was low.
- **Gold's premium follows its properties, not an id:**
  - it does not spoil;
  - it has a very high value per kg, so storing and guarding it costs little per unit of value;
  - it is easy to divide and to test;
  - its yearly flow is small against the stock (Menger on saleability, Kiyotaki & Wright on storage
    cost [memory]).
- **Stock-held demand pins the price.** If households hold a money value of metal, the price is the
  money held over the stock, and a year's mining moves it little. The gold/silver ratio then emerges
  from portfolio weights and stock sizes, and nothing fixes it. Barsky & Summers 1988 treat gold as
  an asset priced as an asset [memory].

## The rule (sim/economy only, keyed on GoodSpec fields and prices)
- **Candidates.** A good counts when it is durable (`service_life_years > 0`, which needs Complaint
  405), barely spoils, has a mass, and is dense in value against the staple per kg.
- **Choice.** Each candidate is weighted by (1 / carry cost share) ** an elasticity. The carry cost
  share counts spoilage, wear and storage per unit of value. The elasticity must stay below one:
  otherwise a price rise raises its own demand.
- **Target.** A share of the savings target, rising with expected inflation and falling with the
  real rate, capped.
- **Buying.**
  - Bids are placed after needs, only when the stock held is below the target less a band.
  - They come out of the same pot as the funds households lend.
  - The stores held count toward the wealth households spend from.
- **Selling.**
  - The excess above the target plus the band is offered at the holding reservation.
  - In a shortfall, enough is offered cheaply to buy the food floor (the hoard as a dearth buffer).
- **Opening stocks** are seeded from the opening savings, so year one does not bid against the flow.

## Risks
- **A deflationary sink** where the store is also the money's metal. The mint's standing orders bound
  it, and it is watched with `money_audit`.
- **The money's own metal is pinned by the mint**, so the ratio moves through the other metal.
- **A liquidity trap.** The liquidation rule covers it, with a test of the unmet floor.
- **Positive feedback.** The elasticity limit covers it.

## Steps, each with a fixture test
1. Durable goods in the fixture (service lives).
2. `households_store.store_candidates`.
3. `store_value_target`.
4. Store bids in `households_orders.goods_orders`.
5. Rebalancing and liquidation offers.
6. Opening stocks in `opening.py`.
7. Behaviour: the ratio of the dense to the cheap metal is above one; its volatility is below a
   flow-priced control's; a mint-parity case shows no runaway.
