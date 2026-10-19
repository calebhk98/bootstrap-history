# Small lenders should pool instead of each lending to every borrower

**Status:** closed

Follow-up to 575. A facility draw was split across every lender in proportion to its offer, so every firm held a
claim on every other firm and the claims, and a year's postings with them, grew with the square of the firms. 575
stopped the growth with a stand-in (`LENDER_MATERIALITY` in `sim/agents/purses.py`): a lender whose offer is a
small share of all the funds on offer takes no part in a draw, and the savers' pool covers its part.

Why it matters: firms that have spare cash and lend it to other firms no longer do so unless their offer is a
material share, which understates firm-to-firm credit in a game where the savers' pool is small.

What it would take: an intermediary (a bank or a merchant's credit) that pools small lenders' funds and lends
them as one counterparty, so small lenders earn interest again without a claim per borrower. Retire
`LENDER_MATERIALITY` with it. Measure the stand-in with `python3 sim/constants.py --burndown`.

## Resolution

Lending goes through one pool, `POOL` in `sim/agents/purses.py`, a counterparty in the actors' book. A lender (a
firm's spare cash, the state's reserve) holds one deposit contract (`DEPOSIT` in `sim/contracts.py`); the household
savers deposit whatever the pool lacks and are paid back what it holds beyond its lending. A borrower holds one
facility claim of the pool, whatever the number of lenders. An actor short of cash takes back its own deposit first,
then draws. Interest a borrower pays stays in the pool until `settle_interest` (once a year, at the lenders'
meeting) shares it among the depositors in proportion to their deposits, a posting per depositor. A default drops
the claim and scales every deposit down in proportion, so the loss is booked once. `LENDER_MATERIALITY` is gone
(`python3 sim/constants.py --burndown` no longer lists it), and a small firm's spare cash earns interest again.
Regression tests: `sim/tests/test_pooled_lending.py` (counts of contracts and postings against borrowers plus lenders).
