# Screens repeat long explanations every time; completions print twice

**Status:** open

- About a third of every `why` screen (14 of 41 lines at 119 AD) is the same "staff to keep it open is a share of a year, not a headcount" paragraph.
- The "YOUR PRACTICE ... pays about a third ..." paragraph repeats on `money`, `ventures` and `help money`.
- Each `start` on credit prints a ~20-line forecast and "total committed" block; three starts = three blocks.
- Each completion prints twice per step (`COMPLETED`, then `DURING ... completed: ... STATUS: CLOSED / NOT OPERATING ...`).
- "population still N% below trend" every year; "<concern> has N spare craftsmen before it closes" once per concern with the same household-wide N.
- NAME is cut to 20 characters in tables ("Establish a respecta").
I filtered most output with grep to find the line that mattered.

What it would take: a verbosity setting (explain once, then one-line pointers); dedupe completion lines; one household-wide staffing line; wider or wrapped names.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

Update: the `available` table gained NET/YR, PAYB and FOREMAN columns (162, 149), and NAME is now cut to 14 characters to keep the width near 130. Names are harder to read than before; wrapping or a second line for long names would fix both.
