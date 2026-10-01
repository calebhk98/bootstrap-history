# Mine stock on hand grows faster than the stated flow, then stops

**Status:** closed - stock is now banked once per year (opening-of-year snapshot); RATED/ACTUAL/UTIL defined on the `mines` screen

`mines` reported a galena working at 280 t/yr, ready in 123 AD. `materials` at 129 AD showed 6,993 t on hand with YOUR FLOW 279.5: about six years of output should be ~1,700 t, and 6,993 is exactly 25x the yearly flow. After one more `step 1` it read 6,992: no growth although flow still said 279.4 and nothing consumed it.

Also on `mines` (582 AD): a coal working shows RATED 18,000, ACTUAL 30,166, UTIL 9%. It is unclear how output exceeds the rating while 9% is used.

What it would take: check the stock accounting for own workings against the rated flow per year; define the RATED/ACTUAL/UTIL columns on screen.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

**Resolution.** The stock ledger was re-banked on every recompute of the year's materials whose inputs differed (any `sell material`/`buy material`, which clears the cache, or a changed project or mine), so each such call added another year of output and also drew demand again. Reproduce: `python3 sim/test_regressions.py --only mine_stock_accounting` (25 one-tonne sales in one year took a 280 t/yr working from about 1,400 t to about 8,400 t, the reported 25x). `resource_throttle` now works from an opening-of-year snapshot (`_material_opening_stock`, saved in `economy._material_stock_opening`), which trades adjust, so the year's output is banked once. On `mines`, RATED is tonnes/yr sunk, ACTUAL is tonnes/yr raised now (rated, less depletion, times mining technology, so it can exceed RATED), and UTIL is the share of ACTUAL that demand draws (it was drawn over RATED, which is how 9% sat beside ACTUAL above RATED); a legend line says so on the screen.
