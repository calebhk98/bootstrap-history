# The non-labour part of a carriage fee (feed, carts, ships, animals, losses) goes to the poorest households of the source tile

**Status:** closed - the fee is split by supplier: crew by the labour market, carriers worn and the feed the team's animals eat bought by the merchant in the goods market (`sim/economy/carriage_wear.py` rows; geography's `animal_feed_kg_per_tonne_km`), the rest (carrier interest, losses, margin) kept by the merchant that owns the carriers and drawn by its owner as profit; nothing goes to the poorest of the source tile. Tests: `sim/tests/test_carriage_fee_parts.py`.

Left: where a setup names no carriers the old payout to the poorest remains (hand-built fixtures only); crew pay for a merchant's first shipping year (no plan, so no hours hired) is still paid to the poorest of the source tile until that year is planned; the loss part of a fee is not separated from the margin (spoilage books goods lost, but a carrier lost on the road has no mechanism yet; 631).

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 631.

**What is wrong.** After the crew's wages, the rest of the fee is paid to the poorest households of the source tile, which supplied none of it.

**Evidence.** `dispatch_merchants` in `sim/economy/year_close.py`.

**Why it matters.** Money should reach those who supply the feed, carts and animals.

**What it would take.** Pay each part of the fee to the supplier of that part through the market.

**Test.** A test: the fee's non-labour part appears as purchases of feed and vehicle goods, not as payments to the poorest.
