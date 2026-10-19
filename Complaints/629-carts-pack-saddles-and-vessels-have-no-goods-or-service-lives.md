# Carts, pack saddles and vessels are not goods and have no service lives

**Status:** open

Part of Complaint 552 (Carriage pays the poor without using their hours or any carriers).

Depends on 617 (ships and shipwright).

**What is wrong.** Only `ox` and `mule` exist, without service lives.

**Evidence.** `data/production/`; the "Sized" section of 552.

**Why it matters.** Carriers as capital need goods that wear (CLAUDE.md 4.3).

**What it would take.** Cart, pack saddle and vessel goods with recipes and sourced service lives, and service lives on `ox` and `mule`.

**Test.** `validate` passes; a test reads the service lives.
