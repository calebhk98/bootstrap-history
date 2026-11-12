# Household spending rests on stored figures with no pre-modern source


**Status:** partly - the years-of-surplus-income wish is deleted; the Eurace consumption budget's figures are sourced to Eurace's manual, not to a pre-modern society

Part of Complaint 526 (The opening's income leaks saving, so the economy opens at subsistence and its wage keeps falling).

**What is wrong now.** A household's yearly spending is Eurace@Unibi's live consumption budget
(`households_buffer_stock.spending_budget`, called from `households_orders.goods_orders`): mean net income plus a
yearly share of cash and claims plus a share of share wealth above a target. The savings wish it replaced
(`SAVINGS_YEARS_OF_SURPLUS_INCOME`, `SAVINGS_RESPONSE_FLOOR`, `SAVINGS_RATE_RESPONSE_LIMIT`) no longer exists. What remains is
unsourced for any pre-modern society:

- `CARROL_CONSUMPTION_PARAMETER` and `WEALTH_INCOME_RATIO_TARGET` (`households_buffer_stock.py`) carry the Eurace manual's
  values (section 10.1.3), one value for every household; the Eurace C code sets no default.
- `WEALTH_DRAWDOWN_LIMIT`, `SPENDING_CUT_LIMIT` (`households_orders.py`) and `HOUSEHOLD_TIME_PREFERENCE` (`household_time_preference.py`) say "no source found"; their `retire` points to 607, only the two Eurace constants above point here.
  `HOUSEHOLD_TIME_PREFERENCE` now also sets every civilisation's opening interest rate: `opening_rate.opening_market_rate`
  clears no funds against no requests at the opening (the resting opening gives households no spare cash), so it returns
  the lenders' lowest ask, which is this figure. Until the opening has lenders and borrowers to clear, the opening rate is
  this unsourced figure.
All are declared `temporary_heuristic`; `python3 sim/constants.py --burndown` lists them and their `retire` entries.

**Why it matters.** An unsourced stored figure that moves the whole opening is a hardcoded outcome (CLAUDE.md 4.1, 4.4).

**What it would take.** A read source for pre-modern household saving and wealth held as a multiple of income (probate
inventories, dowry records, economic-history estimates), then keep or change each figure with the source recorded on the
constant. Re-measure the settled ratio with `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`.

**Test.** Each constant above carries a source and, while a heuristic, a `retire` entry; a test pins the settled ratio band.

**Sourced so far.** `Complaints/reports/research-pre-modern-interest-rates.md`: national wealth in France and Britain around
1700 was several times national income and mostly land, with coin a small share (Gregory King for England). Household-level
multiples from probate: no source found.

Opened for this complaint:

- `HOUSEHOLD_TIME_PREFERENCE`: Clark, Econ 110A chapter 9 (`faculty.econ.ucdavis.edu/faculty/gclark/ecn110a/readings/chapter9.pdf`),
  Table 2: English rent-charge returns stay between 4.0 and 6.0 percent in each half-century from 1451 to 1800; the text cites
  anthropologists for a Malthusian time preference of 2.3 to 2.8 percent. The stored value sits inside the observed English safe
  range and is recorded on the constant. It stays a `temporary_heuristic`: English, post-1450, and a lender's rate, not a
  measured household time preference.
- `WEALTH_INCOME_RATIO_TARGET`: Gallman and Rhode, "Wealth in the Colonial and Early National Periods"
  (`nber.org/system/files/chapters/c14402/c14402.pdf`, p. 297 to 298), summarising Jones's 1774 probate sample: wealth is
  physical wealth with financial assets and liabilities excluded, and specie is $4 million against Blodget's $600 million total.
  No wealth-to-income multiple for liquid or financial wealth is given. Still no source found.
- `CARROL_CONSUMPTION_PARAMETER`: Carroll 1997 (QJE 112) was seen only in search summaries, which give no monthly spending
  share out of wealth; not opened, not cited. Still no source found.
- `WEALTH_DRAWDOWN_LIMIT`, `SPENDING_CUT_LIMIT`: nothing found in any source opened.
- Blocked (HTTP 403): the Exeter and Cambridge pages on probate wealth and indebtedness (`core.ac.uk/download/161940745.pdf`,
  `campop.geog.cam.ac.uk/.../paper29.pdf`); Overton et al. 1600-1750 was not reachable beyond catalogue pages.

**Update (sourcing pass).**
- `SPENDING_CUT_LIMIT` (0.3): sourced, confidence C, no longer a heuristic. Frankenberg, Smith and Thomas, "Economic shocks, wealth and
  welfare" (ccpr.ucla.edu/wp-content/uploads/2024/04/Economic-shocks_-wealth-and-welfare.pdf, opened): Indonesia 1998, "on average,
  household per capita consumption declined by around 20% in one year" (text elsewhere: "almost 25%"); deferrable items "declined by over
  one-third".
- `HOUSEHOLD_TIME_PREFERENCE` (0.05): already inside the opened Clark range (4 to 6 percent English safe returns); confidence raised
  to C. It stays a heuristic because it sets the opening rate, which should be an output.
- Still unsourced: `WEALTH_DRAWDOWN_LIMIT`, `CARROL_CONSUMPTION_PARAMETER`, `WEALTH_INCOME_RATIO_TARGET`. Tried and nothing usable: Wikipedia
  Consumption smoothing and Time preference (no pace or ratio figures); the Quisumbing and Skoufias consumption-insurance synthesis
  (opened; regression coefficients only, no drawdown pace); Kazianga and Udry, Hoddinott, and World Bank pages (HTTP 403 or 503).
