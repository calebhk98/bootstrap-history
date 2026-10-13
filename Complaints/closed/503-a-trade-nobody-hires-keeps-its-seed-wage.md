# A trade nobody hires keeps its seed wage, so scribes cost many times a scholar

**Status:** closed - a trade that hired no hours is priced as unskilled wage times its training premium

On the `market` screen of a Rome game (`play --civ rome_100ad --kit merchant --seed real25`), a scribe's
year costs dozens of times a scholar's, and dozens of times a labourer's. Scribes were rarer than labourers,
so a premium is right, and the engine's own wage schedule gives one of about two to one. The screen's figure
comes from a stale seed, not from scarcity.

Cause:

- `wage_per_hour` (`sim/engine/economy_port_year.py`) uses the agent economy's wage for any trade that
  economy has. A trade it lacks gets the unskilled wage plus its training premium.
- Scribe is in the economy's wage table only because the written-page recipes
  (`data/production/99_writing_pages.json`) name scribe labour. No producer actually hires scribes.
- With no hours hired, `wages_by_trade_weighted` (`sim/economy/api.py`) falls back to the unweighted mean of
  the trade's remembered wages. Nearly all of those are still the opening seed. Meanwhile the wages that do
  clear fell well below the opening scale, so the seed now sits far above every real wage.
- The labour scarcity factor is capped (`_price_factor_from`, `sim/labour/labour_market_api.py`), so
  scarcity cannot explain the gap.

Why it matters: every project and institution that hires scribes is overpriced by the same factor. 475
says the state's tax collection is costed at scribe pay, so this may be much of why the Roman state cannot
pay its army or officials.

What it would take:
- A trade with no hours hired should be priced as `wage_per_hour` prices trades missing from the table
  (unskilled times its training premium), not from the mean of its seeds.
- Separately, find out why cleared wages drift far below the opening scale (473).
- A regression test that every trade's wage on an aged Rome game stays within a bounded multiple of the
  unskilled wage.

## Resolution

`wages_by_trade_weighted` (`sim/economy/api.py`) now leaves out any trade that hired no hours in the scope
asked about, except the unskilled trade, so `wage_per_hour` prices it as the unskilled wage plus its training
premium. Regression tests: `sim/tests/test_unhired_trade_wage.py`. The cause of cleared wages drifting below
the opening scale (473) and the aged-game bound test are not part of this fix.
