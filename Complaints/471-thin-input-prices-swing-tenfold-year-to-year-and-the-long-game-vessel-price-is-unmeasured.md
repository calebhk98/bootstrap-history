# Thin input prices swing tenfold year to year, and the long-game vessel price is unmeasured

**Status:** open

Left from Complaint 434. In the small fixture of `sim/tests/test_economy_vessel_price_fixture.py` (a dug input, clay, fired into a four-year durable), the dug input's price runs between about a hundredth and a tenth of a unit over the 40 years (print it with `PYTHONPATH=. python3` on that test module's `price_path`-style loop, taking `outcome.prices` per year), and the grain price drifts several-fold; the vessel itself stays within about one and a half times its opening price. So the swing is in thin, low-value input markets (a cobweb between capacity and a sold-out raise, `sim/economy/ask_raise.py`, and the markdown of unsold stock), not in the vessels' data.

The earlier claim that ceramic clears near thirteen against about one at the opening of a Rome game after thirty years was not reproduced on a small fixture and not re-measured on a whole game (cold build over ten minutes here). Re-measure it with `sim(civ="rome_100ad")` from `sim/tests/harness.py` aged thirty years, reading the ceramic and clay clearing prices per tile. If it still holds, the cause is in how sellers of thin markets re-price and how entry follows; if it does not, close this with the measured figures.

What it would take: age a Rome game, print the ceramic, clay and firewood prices per tile per year, compare with the fixture's path, and tell whether the swing is damped by entry (`sim/economy/entry*.py`) in the full game.
