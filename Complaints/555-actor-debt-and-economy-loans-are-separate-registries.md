# Actor debt and economy loans are separate registries

**Status:** open

Found by an outside reviewer reading the repository; checked against the code.

- Actors' facility debt is `Purses.claims` (`sim/agents/purses.py`), funded through `EDGE_SAVERS` when a
  purse runs short.
- The agent economy's loans are `EconomyRecord.loans`, with their own clearing, servicing, debts and
  defaults (`sim/economy/credit.py`, `lending.py`, `credit_claims.py`).
- Cash is one book, but a balance sheet is not: a query of one registry misses the other, so an actor's
  total debt, a lender's exposure or a default's losses depend on which registry is asked. No
  contract was found counted in both; the risk is that a rule enforced in one (a credit ceiling, a
  default rule) is bypassed through the other.

## What it would take

- One contract registry with instrument kinds (facility, term loan, state debt from 542), owned by one
  finance module; debts, claims, interest, arrears and defaults derived from it.
- Both current paths moved onto it, one at a time, behaviour-preserving moves kept separate from the
  credit fixes in 547.
- A test: an actor holding both kinds of debt reports one total, and a default books the loss once.
