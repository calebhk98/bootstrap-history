# The non-labour part of a carriage fee (feed, carts, ships, animals, losses) goes to the poorest households of the source tile

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 631.

**What is wrong.** After the crew's wages, the rest of the fee is paid to the poorest households of the source tile, which supplied none of it.

**Evidence.** `dispatch_merchants` in `sim/economy/year_close.py`.

**Why it matters.** Money should reach those who supply the feed, carts and animals.

**What it would take.** Pay each part of the fee to the supplier of that part through the market.

**Test.** A test: the fee's non-labour part appears as purchases of feed and vehicle goods, not as payments to the poorest.
