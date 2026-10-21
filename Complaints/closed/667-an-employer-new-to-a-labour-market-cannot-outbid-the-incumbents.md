# An employer new to a labour market cannot outbid the incumbents

**Status:** closed - employers are ranked by their maximum bid (`clearing.standing`); the wage paid still follows the clearing rule and the ceiling

Found while fixing `economy_carriage_hours` (its tests were rewritten to the rule: `clearing.clear_one` on built
inputs). The labour core keeps incumbent hires first, and the market wage is held under the import and substitute
ceiling (`trained_substitute_wage`, `sim/labour/market/clearing.py`). An employer with no hires in a market (a
merchant hiring carriers, an entrant firm) therefore gets hours only from what incumbents leave, and when incumbents
take the whole supply it gets nothing even with a maximum bid far above the wage: the probe saw a merchant willing to
pay over a hundred times the going wage hire nothing in two of its planned years.

Why it matters: a market where the highest bidder cannot win hours does not allocate labour to its most valuable use.
New firms, merchants' carriage and every expansion depend on drawing hours away from existing uses (CLAUDE.md 4.1:
labour scarcity must show in who gets hired and at what pay). It also hides demand from the wage: the wage cannot rise
toward the entrant's bid, so trades never look short to people choosing them (664).

Measure: the rule tests in `sim/tests/test_economy_carriage_hours.py` (`clear_one` on a market whose supply incumbents
fill: an entrant at equal pay gets nothing; with a premium it takes hours).

What it would take: decide the rule from the labour-market design (docs/architecture, sim/labour/market): either
incumbents keep hires only up to the wage the highest bidder would pay (they lose hours to a higher bid), or the
ceiling caps what is paid but bids above it still rank employers. A function test on built inputs that an entrant
whose maximum bid beats an incumbent's takes hours from it.


## Finding

Employers were grouped and served by the wage they paid, which the ceiling caps, so an entrant bidding far above the
incumbents paid the same as they did and ranked level with them. Fix (`sim/labour/market/clearing.py`): `eligible_bids`
also returns each employer's `standing` (its maximum bid raised by the premium it offers) and `hire_new` and `poach`
rank and draw by it. `market_wage`, the ceiling and the wage paid are unchanged, so Complaint 651's step (and its test)
is untouched. The incumbent's edge is what the engine already models: retained hours first, and the matching friction
and `ON_THE_JOB_SEARCH_SHARE` per year, so a higher bidder takes hours over a few years, not at once. Equal maxima still
leave an entrant nothing. No hiring cost is added: none has a source, and standing is a stand-in for the entrant's own
means of drawing hours, noted in its docstring. Test: `sim/tests/test_labour_core_bid_ranking.py` (an entrant with a far
higher maximum takes hours from the incumbent; a lower maximum takes none; the wage paid stays at the clearing wage).
