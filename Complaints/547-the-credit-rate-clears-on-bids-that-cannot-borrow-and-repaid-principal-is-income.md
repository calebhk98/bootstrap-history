# The credit rate clears on bids that cannot borrow, and repaid principal is counted as income

**Status:** open

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
