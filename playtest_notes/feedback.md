# Playtest feedback and requests

General impressions and wishes from a new-player run (Rome 100 AD, poor_scholar kit).

## Onboarding
- The intro and `help` are thorough and honest about the traps (open vs finished, practice income, calendar floors). They are also very long; almost every screen repeats multi-paragraph explanations (e.g. the "venture_hands is a share of a year" paragraph appears in full on every `why`). A `verbose off` switch, or showing each explanation once and then a one-line pointer, would make screens scannable.
- Request: a NET/YR column (earns minus upkeep) in `available`, and `sort net`. The single most useful early question is "what pays back fastest", and today you have to do the arithmetic by eye across pages.
- Request: a payback-years column, or `available sort payback`.

## Money
- The `start` reply's credit forecast is good, but three starts in a row print three near-identical multi-paragraph "total committed" blocks. One summary after a batch would do.

## Staff
- When a foreman (the one carpenter who supervises the loom) dies or leaves, every concern they watched closes that year, with no warning beforehand. Request: warn in `state` when a concern depends on exactly one person ("single point of failure"), and/or an `auto_replace` policy that re-hires the same trade when a foreman is lost. `auto_hire` only replaces taught trades.
- It is unclear which trade supervises which concern until `open` refuses. See bugs.md #4. A FOREMAN column in `available`/`why` would fix it.

## How much each command tells you (measured at 119 AD, seed-1 save)
Screen lengths (non-blank lines): `why lens_grinding` 41, `state` 42, `money` 54, `ventures` 60, `start fin_trademark` 20.
- About 14 of the 41 lines on every `why` are the same "staff to keep it open is a share of a year, not a headcount" explanation, word for word, on every item.
- The "YOUR PRACTICE ... pays about a third ..." paragraph repeats on `money`, `ventures` and `help money` every time.
- Every `start` that dips into credit prints a ~20-line forecast plus a "total committed" block. Three starts in a row = three near-identical blocks.
- Each completion appears twice per step (`COMPLETED 108: X` then `DURING 108: completed: X. STATUS: CLOSED / NOT OPERATING ...`).
- "population still N% below trend ..." prints every single year.
- "<concern> has N spare craftsmen before it closes" prints once per concern with the same N, because it is a household-wide figure.
In practice I grep-filtered most output to find the one line that mattered.

## Where one command was not enough
- **Picking an earner** took five commands and a refusal: `available` (paged; `sort earns` broken, bugs.md #1) -> `why` (gives the wrong staff, bugs.md #4) -> `start`/`step` -> `open` (refused: needs a carpenter) -> `labour carpenter` -> `hire`. The foreman trade only shows up in `ventures` after the concern is open.
- **Pricing a raw material:** I still do not know what a tonne of charcoal costs at market. `quote` takes only mine/forest/people, `economy full` lists only materials "above book price" (none), `materials` is empty until you hold stock, and `buy material` has no dry-run. Request: `quote material <name> <tonnes>`.
- **Unit ambiguity:** `quote mine galena 100000` prints "tonnes per year: 100,000" for a material whose key is `galena_kg`. Only by re-quoting at 280 and 1 could I tell that the input is tonnes.

## Command count
There are about 45 commands. The ones I actually needed: state, path, available, why, start, step, open, ventures, money, labour, hire, quote, economy (13). The hints after each screen point to the right next command well, so remembering them was not the problem.
The friction is inconsistent nouns between sibling commands: `buy` takes farm/housing/school/material/nitre, `quote` refuses all of those, and `help commands` lists `options` as an alias for `available`.
