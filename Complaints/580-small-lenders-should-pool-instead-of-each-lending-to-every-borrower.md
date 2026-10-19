# Small lenders should pool instead of each lending to every borrower

**Status:** open

Follow-up to 575. A facility draw was split across every lender in proportion to its offer, so every firm held a
claim on every other firm and the claims, and a year's postings with them, grew with the square of the firms. 575
stopped the growth with a stand-in (`LENDER_MATERIALITY` in `sim/agents/purses.py`): a lender whose offer is a
small share of all the funds on offer takes no part in a draw, and the savers' pool covers its part.

Why it matters: firms that have spare cash and lend it to other firms no longer do so unless their offer is a
material share, which understates firm-to-firm credit in a game where the savers' pool is small.

What it would take: an intermediary (a bank or a merchant's credit) that pools small lenders' funds and lends
them as one counterparty, so small lenders earn interest again without a claim per borrower. Retire
`LENDER_MATERIALITY` with it. Measure the stand-in with `python3 sim/constants.py --burndown`.
