# A starved market never grows, because entry is sized to what it traded

**Status:** open

Found tracing copper (511, Update 3). `entry_sizing.sized_runs` caps a newcomer at
`ENTRY_SHARE_OF_TRADED_VOLUME` of last year's traded volume. A market whose makers are too small trades almost
nothing, so the newcomer it allows is almost nothing: Rome's Algerian flux market traded a few kilograms, and a
gap of more than a run of flux sized a newcomer at a small fraction of a run. Copper smelters there get a fraction
of the flux they plan for, their runs collapse, and copper stays several times its cost.

The cap is pinned on purpose (`test_economy_entrant_sizing`, "a gap far beyond the trade is sized to the
trade") so a phantom gap does not build a works. What is missing is a way to tell a starved market from a phantom
gap: buyers' bids that went unfilled at prices above the newcomer's full cost are real demand; a gap no bid backs
is not.

What it would take: size entry from the unfilled bids that would pay the newcomer's full cost (the year's order
book holds them), keep the traded-volume cap only where no such bids exist. Tests: a market with unfilled bids
above the entrant's cost admits a newcomer sized to those bids; a gap no bid backs is still sized to the trade.
Related: 511, 512.
