# The credit rate clears on bids that cannot borrow, and repaid principal is counted as income

**Status:** closed

Found by an outside reviewer reading the repository; both reproduced here.

1. **Negative bids set the rate.** `credit.clear` (`sim/economy/credit.py`) takes each request's
   ceiling as its maximum rate less its risk premium. With no collateral the premium can exceed the
   maximum rate, the ceiling goes negative, and `clearing_point` uses it anyway. Reproduction:

       python3 -c "from sim.economy.credit import clear; from sim.economy.types import LoanRequest, FundsOffer; print(clear([LoanRequest('b','c',100.0,0.05,2,0.0,'x')], [FundsOffer('l','c',1000.0,0.0)], 'c', 0.01, {'b':0.0})[:2])"

   From a 1% rate it returns a negative rate and no loans. Household subsistence loans carry zero
   collateral (`sim/economy/households_credit.py`), so this is the ordinary case. This is a likely cause
   of the rate that decays toward zero and jumps (527).
2. **Principal is income.** `lending.service` (`sim/economy/lending.py`) returns everything a lender
   received, and `Economy` adds it to `record.property_income` (`sim/economy/economy.py`). A payment of
   principal plus interest counts whole as income, though returned principal only turns a loan back
   into cash. Property income drives consumption and saving.

## What it would take

- Regression tests for both reproductions first.
- Requests whose ceiling is below every lender's ask are rationed demand, left out of the clearing and
  reported as unmet.
- Service transfers split into interest, principal and arrears; only interest (and arrears interest)
  is property income.

## What now happens

- `credit.clear` leaves out of the clearing every request whose ceiling is below zero or below every
  lender's ask. Such a request is rationed demand: it stays in the returned unmet list (amount untouched)
  and gets no loan. The base rate is never below zero.
- `credit.service_split` returns each lender's receipt as a `Receipt` (interest, principal, arrears);
  `credit.service` keeps its old shape. `Loan.arrears_interest` records which part of arrears is unpaid
  interest; a payment clears arrears interest, overdue principal, this year's interest, then the
  installment. `lending.service` returns interest only, so `Economy` adds only interest to
  `record.property_income`.
- Tests: `sim/tests/test_economy_credit_rationing_and_service_split.py`. The lending test that expected
  principal plus interest as the lender's receipt now expects interest only.
