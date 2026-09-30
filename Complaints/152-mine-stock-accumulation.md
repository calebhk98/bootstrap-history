# Mine stock on hand grows faster than the stated flow, then stops

**Status:** open

`mines` reported a galena working at 280 t/yr, ready in 123 AD. `materials` at 129 AD showed 6,993 t on hand with YOUR FLOW 279.5: about six years of output should be ~1,700 t, and 6,993 is exactly 25x the yearly flow. After one more `step 1` it read 6,992: no growth although flow still said 279.4 and nothing consumed it.

Also on `mines` (582 AD): a coal working shows RATED 18,000, ACTUAL 30,166, UTIL 9%. It is unclear how output exceeds the rating while 9% is used.

What it would take: check the stock accounting for own workings against the rated flow per year; define the RATED/ACTUAL/UTIL columns on screen.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
