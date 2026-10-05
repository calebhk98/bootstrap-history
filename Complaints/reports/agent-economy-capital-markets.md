# Capital markets on the agent economy

Design note for Complaint 106. It describes `sim/economy/` as it is, not the old engine market
(`sim/engine/economy_capital_market.py`).

## What exists

- **Supply.** The only source of `FundsOffer` is `households_orders.py`: a cohort offers its cash left after
  its bids and its cash target, at a minimum rate set by time preference plus expected inflation. The state,
  producers and merchants offer nothing, so the state's purse never enters the pool (Complaint 307).
- **Demand.** `lending.py` turns household subsistence shortfalls and merchant cargo into `LoanRequest`s;
  producers queue expansion requests; the state queues a deficit request in `state_finance.py`.
- **Clearing.** `credit.clear` meets offers and requests at one rate per currency. Each borrower pays the base
  rate plus a premium for leverage and remembered arrears, and may be rationed out entirely. The base rate
  moves only part of the way to the clearing rate each year.
- **Claims.** A loan is a `Loan` with a lender, a borrower, a principal and a rate. `credit_claims` values it
  as the lender's asset (principal less doubted arrears) and the borrower's debt. Defaults are lost claims,
  remembered and faded, and they feed the next premium.
- **Conservation.** Disbursement and service are ordinary `Book` transfers. A default moves no money, so the
  book stays conserved.

## What is missing

- **Intermediaries.** Every loan is household to borrower. A cohort lends directly and carries the whole
  default loss, with no pooling and no maturity transformation.
- **Deposits.** Savings are idle cash on the book until a request meets them. There is no deposit as a
  claim, no safe store, no payment by transfer of a claim.
- **Tradable claims.** A loan cannot be sold, so a lender cannot exit early and the state's loans have no
  secondary price. Bonds are only the state's loan with a longer term.
- **Equity.** An owner's stake in a producer is not a claim with a price; dividends exist, shares do not.
- **Runs and crises.** Nothing can fail faster than a borrower defaults, so a lender cascade is slow and local.
- **Insurance.**

## Recommended first step: a bank as an ordinary agent

Add `sim/economy/banks.py` (a small module, with `bank_credit.py` if it grows). A bank is an agent id with a
purse in `accounts.Book` and no special case in the engine; any actor type may found one.

1. **Deposits.** A cohort's offer is sent to a bank instead of to the pool. The money moves from the cohort's
   purse to the bank's purse. The bank owes the cohort a deposit claim. Record it as a `Loan` with the
   cohort as lender and the bank as borrower, at the deposit rate, in `credit_claims`. Then
   `claims_by_lender` already counts it in the depositor's wealth, `debts_by_borrower` counts it against the
   bank, and `credit.service` pays the interest. Nothing new is needed in conservation.
2. **Bank as lender.** The bank emits one `FundsOffer` for its lendable purse, with a minimum rate set
   from its deposit rate plus a margin. Loans to borrowers are ordinary `Loan`s with the bank as lender.
3. **Reserve.** Lendable purse = purse less a reserve held against deposits. A reserve of everything is a
   warehouse bank; a smaller one is fractional reserve. Because the bank lends out of its own purse,
   deposits are never created from nothing here (loans do not create deposits). That keeps the existing
   money-supply conservation untouched, and credit creation is a later, separate step.
4. **Failure.** A bank's repayment is limited by the same `credit.service` cash rule as any borrower. If
   borrowers default, the bank falls behind on deposits and the depositors' claims lose value through
   `claim_value`. A run is then a year in which depositors withdraw: a `Loan` to the bank not renewed. A bank
   with too little purse defaults under the existing rule, so no new failure code is needed.
5. **Visible choices.** The bank's reserve share and deposit margin are its policy fields, so a player or
   another country can run one.

The result is a pool that depends on a bank's choices and not directly on households, and the first place a
loss can land on someone other than the lender who chose the borrower.

Tests (when built): one year of deposit and loan conserves the book to the unit; a defaulting borrower
reduces depositors' claim value and not the money supply; the bank's id appears nowhere in the engine.

## Heuristics this needs (to be declared `temporary_heuristic`)

- Reserve share held against deposits (stands in for liquidity risk and withdrawal behaviour).
- Margin between lending and deposit rates (stands in for operating cost and competition).
- Depositors' choice of bank (stands in for trust and information).
- How much of its capital a bank will lend to one borrower (stands in for concentration risk).

## Later steps, in order

Bonds: let a claim change hands as an ordinary `Book` transfer for a price set by its expected value and
the market rate, so the state's loans trade. Equity: a producer's owner stake becomes a share claim with
dividends as its income. Credit creation: allow a bank to book a deposit against a loan under a reserve
rule, which needs the money supply to count deposits (a decision for `currency.py`). Each of these reuses
`credit_claims` and not a new ledger.
