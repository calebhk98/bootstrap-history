# Insolvent firms never exit

**Status:** closed - a firm whose interest on its debt outruns its margin for `EXIT_LOSS_YEARS` running years (once past its ramp) closes (`firm_exit.interest_outruns_margin`); on closing, the claims lenders hold against it are written off (`Purses.write_off`), so no phantom claim survives. Test: `sim/tests/test_firm_exit_debt.py`.

A firm leaves only when its margin falls below what its plant would earn lent out (`firm_exit`); debt service
is not counted. In the settled game `test_firm_expansion.py` builds, firms with a small positive margin carry
large negative money and debt compounding at the market rate, and stay in business indefinitely.
Exit should weigh what the firm owes, so a firm whose interest outruns its margin closes.
