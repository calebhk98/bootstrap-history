# The number of firms does not grow with the market

**Status:** open

A concern's hands are derived from its takings, so a firm in a bigger market is itself bigger, and the
firm count stays flat or falls as the market grows. `test_firm_count_whole_game.py` now pins the small
game's hands so "a bigger market holds more firms" compares equal-sized firms. Owner decision: should firm
size have a technical optimum (so a bigger market holds more firms) rather than scale with takings?
Measure: the same topic with the pin removed, over several market sizes.
