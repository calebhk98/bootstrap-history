# Thin input prices swing tenfold year to year, and the long-game vessel price is unmeasured

**Status:** closed - the dug input's swing came from sellers reading their laid-out costs as distress (fixed, `sim/economy/seller_cash.py`); the long-game ceramic price does not run away in a Rome game

Left from Complaint 434. In the small fixture of `sim/tests/test_economy_vessel_price_fixture.py` (a dug input, clay, fired into a four-year durable), the dug input's price runs between about a hundredth and a tenth of a unit over the 40 years (print it with `PYTHONPATH=. python3` on that test module's `price_path`-style loop, taking `outcome.prices` per year), and the grain price drifts several-fold; the vessel itself stays within about one and a half times its opening price. So the swing is in thin, low-value input markets (a cobweb between capacity and a sold-out raise, `sim/economy/ask_raise.py`, and the markdown of unsold stock), not in the vessels' data.

The earlier claim that ceramic clears near thirteen against about one at the opening of a Rome game after thirty years was not reproduced on a small fixture and not re-measured on a whole game (cold build over ten minutes here). Re-measure it with `sim(civ="rome_100ad")` from `sim/tests/harness.py` aged thirty years, reading the ceramic and clay clearing prices per tile. If it still holds, the cause is in how sellers of thin markets re-price and how entry follows; if it does not, close this with the measured figures.

What it would take: age a Rome game, print the ceramic, clay and firewood prices per tile per year, compare with the fixture's path, and tell whether the swing is damped by entry (`sim/economy/entry*.py`) in the full game.

## Resolution

Fixture: at the point of sale a producer's cash sits below its target by what it laid out that year; the
distress curve read that as a shortfall and every seller asked a fraction of its expected price, so the thin
clay market fell to those asks in a surplus year and rose to the buyers' ceiling in a shortage year. The
laid-out running costs are now set aside in full (`seller_cash.shortfall_to_raise`), and a buyer's ceiling
clears the market only when what is still wanted just above it fits the supply there (`goods_market`).
`sim/tests/test_economy_vessel_price_fixture.py` bounds the clay price year to year once the market has settled.

Whole game: a Rome game (`sim.tests.harness.sim(civ="rome_100ad")`) aged thirty years, printing each year the
clearing price of ceramic, clay, firewood and wheat over the market areas (the remembered price per area in
`economy.record.memory.prices`; the script was a scratch driver, no committed command). The median ceramic price
stays at its opening value through the thirty years and the dearest area falls back toward it; there is no
runaway of the kind first reported. Clay and firewood prices differ by orders of magnitude between areas,
because an area where nothing trades keeps a remembered price that drifts; that spread is between areas, not
from year to year.
