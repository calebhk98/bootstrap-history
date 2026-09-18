# `temporary_heuristic` conflates "not derived yet" with "copied from history"

**Type:** Registry design / §3.1 compliance
**Priority:** Medium. It makes the burndown harder to act on than it should be.

## The observation

`sim/constants.py` offers six kinds: `physical_constant`,
`biological_parameter`, `engineering_estimate`, `initial_condition`,
`calibration_target`, `temporary_heuristic`. With the engine migration
under way the project now declares **410 numbers, 252 of them
`temporary_heuristic` (61.5%)**, and `sim/engine/economy.py` alone
contributes 208 of those out of its 240.

That single bucket is holding two things that are not alike:

1. **"No mechanism exists yet, so somebody picked a number."** A market
   elasticity, a decay rate, a threshold tuned until the game felt right.
   These are honest scaffolding. CLAUDE.md §3.4 explicitly allows them
   provided they are labelled, and the burndown exists to pay them off.

2. **"A historical outcome was copied in."** This is what §3.1 forbids
   outright, and it is a different thing: not a number nobody has derived,
   but a number that is *the answer* to something the simulation is supposed
   to compute. The two found so far in `economy.py`:

   - `DEBT_BASE_RATE = 0.12` - the Roman legal ceiling on ordinary loans
     (*centesimae usurae*, 1% a month), used directly as the baseline arrears
     rate. It is a real attested figure, which is what makes it dangerous:
     it looks sourced. It is the price of money asserted from the record
     rather than derived from capital scarcity, expected default and lending
     risk. Worse, **every other civilisation reuses it unchanged** - Han
     China borrows at the Roman legal ceiling.
   - `LIVING_COST_TAX_RATE = 0.06` - *portoria*, the *vicesima* and local
     dues aggregated into one flat share of revenue, standing in for a
     state-revenue mechanism that should fall out of trade volume, customs
     enforcement and administrative reach.

Both are correctly labelled `temporary_heuristic` today and both say so in
their `why`. The problem is that they are now indistinguishable, in any
query, from the 250 ordinary scaffolding numbers around them.

## Why it matters

The burndown's whole purpose is to make the migration queue **measurable**.
A queue where "invent a better elasticity eventually" and "a §3.1 violation
is live in the shipping model" sort identically is not measurable in the way
that matters. The second class should be small, should be visible without
reading 252 `why` texts, and should be the thing anyone looks at first.

It also makes the project's own headline claim checkable. CLAUDE.md §3.1 is
the single hardest constraint here - "I don't care if in our history a Roman
soldier cost 100 denarii" - and right now nothing can answer "how many
hardcoded historical outcomes are left?" without a manual read.

## Suggested fix, not applied

A seventh kind, `hardcoded_outcome`, or a boolean flag beside the
kind. Either way `--burndown` should report it separately and loudly, and
the count should be expected to reach zero, unlike `temporary_heuristic`
which will always have a tail.

Do NOT do this as a mass reclassification. The two above were found by an
agent reading its own work carefully, and it flagged that it had initially
declared `DEBT_BASE_RATE` as `initial_condition` before correcting itself -
which is the same confusion one step earlier, and a hint that the boundary
is genuinely hard to see. Finding the rest is a review job, not a regex.

## One thing already checked

Every `physical_constant` in the project was audited when this was written
and all are genuine facts of nature: 9.81 m/s², 4,184 J/kcal, water density,
24 hours in a day, 365.25 days in a year. Nothing is smuggling a historical
figure through the strongest label, which was the first thing worth ruling
out.
