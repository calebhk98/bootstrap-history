# The adviser cannot be told a savings target

**Status:** closed - `saving <id> [amount]` (and `saving off`) records a planned project and cash target on the household (`sim/ui/proto/dispatch_saving.py`, `saving_plan.py`); `stuck` then stops recommending the cheapest startable project and shows a saving row with the year the target is reached at `recurring_net()`, or says never when income does not cover costs. Test: `sim/tests/test_saving_target.py`.

Reported in Complaint 98.
