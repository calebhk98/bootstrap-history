# Carts, pack saddles and vessels are not goods and have no service lives

**Status:** closed - cart, pack saddle and river barge goods with recipes; sourced service lives for them, merchant ship, ox and mule; carriage wears each mode's carrier stock (sim/economy/carriage_wear.py) and merchants bid for replacements; tests in sim/tests/test_carriage_wear.py. Wagons: no mode uses one, so none was added.

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 617 (ships and shipwright).

**What is wrong.** Only `ox` and `mule` exist, without service lives.

**Evidence.** `data/production/`; the "Sized" section of 552.

**Why it matters.** Carriers as capital need goods that wear (CLAUDE.md 4.3).

**What it would take.** Cart, pack saddle and vessel goods with recipes and sourced service lives, and service lives on `ox` and `mule`.

**Test.** `validate` passes; a test reads the service lives.
