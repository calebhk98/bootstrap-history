# Actor debt and economy loans are separate registries

**Status:** closed - one contract registry (`sim/contracts.py`) holds facilities and term loans, with a kind for state debt; the purses and the economy record both sit on it

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

## Resolution

- `sim/contracts.py` is the one registry: `Contract` (lender, borrower, currency, principal, rate, arrears,
  kind) and `Contracts`, with `debt`, `exposure`, `default` and the save records. Kinds are `facility`,
  `term_loan` and `state_debt` (a kind of the same registry; 542 is not done here).
- Path one, the actors' facility: `Purses.claims` is now a read of the registry, and every draw, repayment,
  interest split and write-off goes through `Contracts`. Path two, the economy's loans: `Loan` is a
  `Contract`, and `EconomyRecord.loans` reads the registry's term loans.
- The purses adopt the economy's registry with its book (`Purses.adopt_book`), so one object answers for an
  actor holding both kinds; each owner saves only its own kinds.
- Both moves were checked as behaviour-preserving: a sorted-key JSON dump of the purses (claims, book,
  observer calls, debts) after 300 random postings with a write-off, and of the economy's loans, credit
  losses and remembered defaults over five serviced years with defaults, plus a three-year fixture record,
  were byte-identical before and after.
- `sim/tests/test_contract_registry.py` holds the test: one total from one query for an actor with both kinds,
  and a default that ends the borrower's debt and the lender's exposure by the same amount, once.
