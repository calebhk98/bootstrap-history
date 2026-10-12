# Insolvent firms never exit

**Status:** open

A firm leaves only when its margin falls below what its plant would earn lent out (`firm_exit`); debt service
is not counted. In the settled game `test_firm_expansion.py` builds, firms with a small positive margin carry
large negative money and debt compounding at the market rate, and stay in business indefinitely.
Exit should weigh what the firm owes, so a firm whose interest outruns its margin closes.
