# Debasement cuts the metal in the coin but domestic money prices do not follow

**Status:** closed - a state's cut is a recoinage: the metal saved is struck as more coin (`currency.units_struck_by_cut`) issued to the state, and the lighter average coin follows; prices rise through the money supply and normal clearing. Tests: `state_debasement_prices`, `state_debases_coin`.

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Closed 272 recorded this gap.

**What is wrong.** Debasement cuts the metal in the coin, but domestic money prices fixed at load do not follow.

**Evidence.** `sim/agents/government_coinage.py`; `Complaints/closed/272-han-coin-has-no-debasement-and-uniform-buying-power.md`.

**Why it matters.** A debased coin that buys the same is no debasement.

**What it would take.** Debasement reaches domestic prices through the money supply.

**Test.** A test: after a debasement the domestic price level rises with the money supply, not by a fixed rule.

The twin-economy price-level check (a debasing state against one that did not, four fixture years) is not a unit test and was deleted. The unit rules are `units_struck_by_cut`, `debase_by_cut` and `Economy.strike_lighter_coin` in `test_state_debases_coin`. No simulator command measures the price effect; compare two `Economy` runs of the fixture setup differing only in the yearly `strike_lighter_coin` cut.
