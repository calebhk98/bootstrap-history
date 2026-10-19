# A mid-game year costs many times an early year

**Status:** open

Found after closing 575, on the legitimate agent playtest's save (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`,
Rome, seed 11, 143 AD, about thirty concerns running): a year from that save takes minutes, where the same game's
years near 100 AD took seconds. 575's profile puts most of the rest in price calculation.

Why it matters: the release criterion is a whole game played by an agent; a year whose cost grows with the game's
activity makes the second and later centuries unplayable however fast the opening is. Complaint 497 tracks the
opening's per-year cost; this is the growth on top of it.

What it would take: profile a year from a mid-game save, find which costs grow with the number of concerns, firms,
plants, contracts or recorded history rather than with the year's own activity (caches keyed on state that changes
every year, solves repeated per concern, histories kept and scanned), and make them linear in the year's activity;
a test on call counts that a year's work does not grow with the number of past years.
