# Household spending rests on stored figures with no pre-modern source


**Status:** closed - every constant it names carries an opened ballpark source

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

**Update 2.**
- `WEALTH_INCOME_RATIO_TARGET` (16.67 months of income): order of magnitude sourced, confidence C. Piketty and Zucman, Handbook of Income
  Distribution ch. 15 (gabriel-zucman.eu/files/PikettyZucman2015.pdf, opened): European aggregate wealth "as large as 600-700%" of national
  income in the 18th-19th centuries, "Agricultural land ... made the majority of national capital", durable goods 30-50% of national
  income. 1.4 years of income held as share wealth sits well below that. Household-level multiple still unmeasured.
- `CARROL_CONSUMPTION_PARAMETER`, `WEALTH_DRAWDOWN_LIMIT`: still no figure. Opened: Carroll's tractable buffer-stock notes and age-profile
  handout (econ2.jhu.edu/people/ccarroll/public/LectureNotes/Consumption/; no calibrated parameter values in the text); Laibson and Maxted,
  MPC to MPX note (quarterly MPX on nondurables 15-25%, a windfall response, not a monthly share of cash above target); LEGS drought
  briefing (qualitative: pastoralists "try to protect a core herd"). The Indonesia paper gives share of households that sold all gold
  (over half rural, a third urban) but not a share of wealth drawn down per year.
Status stays partly.

**Update 3.**
- `WEALTH_DRAWDOWN_LIMIT` 1.0 to 0.7, confidence C: Indonesia 1998 (Frankenberg, Smith and Thomas, opened): over half of rural and close to one-third of urban gold-owning households sold all their gold in one crisis year. Take half of the store as the most drawn in a year; the store is the wealth target, 1.39 years of income: 0.5 * 1.39 = 0.69.
- `WEALTH_INCOME_RATIO_TARGET`: order of magnitude sourced (Piketty and Zucman), confidence C, no longer a heuristic.
- `CARROL_CONSUMPTION_PARAMETER` stays 0.01 (Eurace). Laibson and Maxted's quarterly nondurable MPX of 15-25% converts to a monthly 0.072, but at that value the yearly cash share is near 0.6 and the cash cap or the drawdown limit always binds before wealth, so money lent stops moving spending; five test topics fail on it (economy_credit_claims, household_buffer_stock, money_reaches_prices, saving_finds_a_use_rule, household_savings_smooth). A windfall MPC is not a rate of spending out of the stock; this needs the rule redesigned (the method the `retire` names), not a number.
Status stays partly: only `CARROL_CONSUMPTION_PARAMETER` is left.

**Update 4 (closed).** `CARROL_CONSUMPTION_PARAMETER` keeps 0.01 a month (0.114 a year), confidence C, bracketed by the marginal propensity
to consume out of wealth: Wikipedia "Wealth effect" (citing Carroll and Zhou) 6 cents per dollar of home equity a year; Jorgensen,
Danmarks Nationalbank Working Paper 112 (2017, annual data) aggregate MPC out of liquid assets 49 percent. Cash lies between, and 0.114 is inside.
