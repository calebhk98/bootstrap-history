# A starved market never grows, because entry is sized to what it traded

**Status:** closed - the sizing rule is built and tested; the starved Rome flux market no longer reproduces with the short or the full spin-up

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

## Update 1: unfilled bids at the entrant's full cost now count with the trade

Built: `sim/economy/entry_backed.py` (`unfilled_at_cost`) takes the year's order book (`ledger.bids_by_market`, which
`open_entrants` already receives) and, per recipe and market, the quantity the bids take at the recipe's full cost per
unit (`entry_trial.full_cost_per_unit` through `recipes_by_cost`; a buyer whose `maximum_price` is below the cost takes
nothing) less last year's traded volume. `entry_sizing.sized_runs(..., unfilled=)` sizes the newcomer to the share of
trade plus that unfilled quantity (where nothing traded, the larger of the trial size and the share of the unfilled
quantity). The share of the gap stays the upper bound, so a gap no bid backs is still sized to the trade and bids never
build beyond the gap. No new constant: the existing share is reused. Tests: `test_economy_entrant_sizing` (sized to
trade plus unfilled bids; to unfilled bids where nothing traded; no bids leaves the pinned cap; never beyond the gap;
the helper counts only bids that pay the cost) and `test_economy_entry_unfilled` (on the small fixture, smelters that
start at a small share of their size end larger after six years with the rule than without).

Measured on Rome (`ROME_SPIN_UP_YEARS=2,1`, five years, probe stepping `Economy` directly; `unfilled_at_cost`
patched out for "before"): flux traded and copper price are identical in years zero to three and within 0.5 percent
in year four (flux traded 120684 against 120085 kg, copper 15.47 in both). Reason: with that spin-up the flux markets'
`unmet` gap is a few kilograms (Italy 2.4, Algeria 5.2, Turkey 6.0 in years two and three) and `sized_runs` is not
called for flux at all, so there is nothing for the unfilled bids to raise. The cap was not what held flux in this
run; the earlier trace (511 Update 3) used the full spin-up, which was not rerun here (over five minutes).
`python3 -m sim.tests --slow --only economy_tin_dearer_than_copper` steps year zero only and entry runs at the year's
close, so it cannot change: it still fails (shown tin over copper 0.047, embodied labour ratio 0.441).
Open: whether the full-spin-up Rome run moves, and why flux entry is not planned there (the recipe may not beat the
interest rate at the remembered flux price).

## Traced on the short spin-up (no change made)

With `ROME_SPIN_UP_YEARS=2,1` and `Economy` stepped directly (probes in the session scratchpad, not kept): Rome's flux
makers are large but idle, holding unsold flux (Algeria's maker stops on `runs_for_stock`); Algeria's copper smelter
holds flux for more runs than it plans and bids only for charcoal; the flux recipe returns well above the interest
rate at the maker's own remembered price; no unmet flux demand reaches `open_entrants`, and where flux bids exist the
trade meets them. So in the short spin-up there is no starved flux market for the sizing rule to act on.

The copper problem there is elsewhere: Algeria's smelter runs nothing in its first years although its capacity is
large, because its expected revenue per run sits just below its variable cost while the market price of copper is
above both. A producer's expectation that lags its own market is the lead for 511 and the `economy_tin_dearer_than_copper`
and `economy_bronze_market_price` failures in 558. Whether the full spin-up still shows the starved flux of 511
Update 3 is being measured.

## Resolution

The rule this complaint asked for is built (Update 1: `entry_backed.unfilled_at_cost`, `entry_sizing.sized_runs(...,
unfilled=)`, tests `test_economy_entrant_sizing` and `test_economy_entry_unfilled`). The Rome case that prompted it is
gone: stepping the economy after the full-length spin-up, the flux makers of Algeria, Italy and Turkey hold capacity
of hundreds to thousands of runs and run every year, and the short spin-up shows the same. The copper smelters'
shortfall in the first years is charcoal, which no producer makes at the opening: Complaint 570.
