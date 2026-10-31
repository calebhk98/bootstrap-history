# A trade that has never existed has no way to form

**Status:** partly - first hands, migration, an owners' ask and a buyers' bid for bonded people, held bonded, carried between areas by merchants and a learning-curve rule and its wiring into a producer's hours are built; a trade whose work is a service, the curve's wiring into spoilage, and more `taught_from` links are open (see What is wrong now)

**What is wrong now.**

- A trade no recipe books hours to (optician, scholar, soldier, sailor, dockworker, master) has no task description, so no source trade covers it and it trains at the full apprenticeship with no early hands. The service it sells has no demand side the formation reads: its first hands should come from the people who demand the service (an unmet need for it pulling hands in), and no data or economy reading names that demand yet.
- The learning curve now sets a producer's hours (item 9) but not its spoilage: `learning_curve.error_share` is still called by nothing in the economy. `train_check` does not pass the teacher's proficiency to `trade_first_hands.cohort_rows`. `SOURCE_TASK_FLOOR_FRACTION` therefore stays a labelled heuristic.
- `taught_from` in `data/world/trades.json`: one link was added with an opened source (millwright from carpenter). No opened source supports electrician, engraver or the other trades without a link; Wikipedia's Electrician page says only that electricians "were originally people who demonstrated or studied the principles of electricity".
- Bought bonded people arrive in the area's workers at a trade; the engine holds them for the buyer's works through `record.bonded_held`, but a person is a headcount (strata count all ages, the labour core working people), and the keep the holder pays is the area's wage floor, not a measured cost of keeping a bonded household.

**What it would take.** Output and error following a learning curve with a physical floor for any actor and trade; a
first cohort whose start is capped by the teacher; the owners' sale rule from the owner's own choice. Tests call the
training functions: a trade with no teacher stays empty; a nearer source trade trains faster.

**Sources.** `Complaints/reports/research-how-a-brand-new-trade-forms.md`: the first hands of a new trade came from the
nearest trades (Boulton and Watt's from millwrights, smiths and instrument makers), trained inside the inventor's firm on
narrow tasks; it was slow and early work was poor. Skill distance between occupations is measured from task content
(Gathmann and Schonberg). Learning curves: Wright 1936 with quality change and spillovers (Thompson; Thornton and Thompson).
How an existing trade spreads is in `research-how-trades-spread-and-skill-premia.md`.

**Research needed.** A sourced price of a trained bonded craftsman against an untrained one (Roman or Atlantic sale records): Scheidel
2005 (JRS 95, read in the Gwern copy) says only that "Republican slave prices are unknown" (note 82) and defers real prices to a later
paper, so the owner's ask here is derived from the present value of the hours (Complaint 644 item 3 above), not checked against
sale records. See also 648.

## Built (one line each)

1. `sim/labour/trade_formation.py`: task shares per trade from the hours recipes book to it; distance is the cosine angle
   between shares; `first_people_plan` orders migration, conversion and bonded purchase; `train` and `train_check` pick the
   nearest practised trade as source and take time and teacher hours from the uncovered share. Tests: `test_trade_formation.py`.
2. `sim/labour/market/formation.py` runs after migration each year for every (area, trade) with vacancies and no one of the
   trade: migrants from areas with a route in, then bonded people. A trade with some hands and vacancies left buys bonded people
   too. Tests: `test_trade_formation_routes.py`.
3. Owners' sale rule and the bonded price (`sim/labour/market/bonded_worth.py`, `formation_bonded.py`): a person is worth the
   present value of their hours over a working life at the household discount rate (`worth_of_hours`); a trained person's hour
   fetches the trade's wage where it is practised, never less than the floor wage times the trade's training premium
   (`trained_wage_per_hour`), so a trained person is dearer than an untrained one. The owner's ask is that worth where the owner is
   (its practised wage or the premium wage); the buyer's bid is that worth where the buyer is; a person is bought where ask plus
   carriage stays under the bid. `BONDED_SALE_SHARE_PER_YEAR` and `BONDED_PRICE_YEARS_OF_FLOOR` are deleted: every member of a
   bonded stratum is on offer at its owners' price, and how many are bought is the buyers' vacancies. Tests: `test_bonded_worth.py`,
   `test_trade_formation_routes.py`, `test_bonded_purchase.py`.
4. Held bonded (`sim/economy/bondage_hours.py` `hold`, `place_held`; `bonded_purchase.settle`): the employers that bid for the
   trade where the people were bought hold them (`record.bonded_held`); each year their hours come off the households' offers and
   work for the holder, off the market, as far as the holder bids for them; the holder pays their keep to the households whose hours
   were taken. Deaths thin the holding (no more held than the trade's workers there). Tests: `test_bonded_worth.py`.
5. A conversion cohort is written as two training records (`sim/labour/trade_first_hands.py`), now capped at the teacher's
   proficiency (`capped_by_teacher`). Tests: `test_trade_first_hands.py`, `test_learning_curve.py`.
6. `sim/labour/learning_curve.py`: Wright's curve (`unit_time_ratio`, `proficiency`, `cumulative_for_proficiency`), an error share
   with a floor above zero, pooled spillover. `LEARNING_RATE` is sourced (Wright 1936 as stated on en.wikipedia.org/wiki/Learning_curve,
   opened; Thompson, econwpa 9712001, 12 to 24 per cent per doubling in shipbuilding). Tests: `test_learning_curve.py`.
7. Data: `millwright` `taught_from: carpenter` with `taught_from_source` (Wikipedia 'Millwright', opened).
8. Bonded purchase within the plan (`sim/labour/market/bonded_room.py`, `formation_bonded.py`, `sim/economy/outlay_room.py`,
   `bonded_purchase.settle`): a purchase is a capital outlay, so an employer pays only from room its year plan leaves: the cash
   its plan assigns to no line (`YearInputs.outlay_room`: a producer's cash less its wage line and input bids, `Plan.wage_line`;
   the state's cash less its wage and goods budgets and what it holds back, `StateBudget.held_back`) and the wage line of the
   hours it bid for and left vacant. The core shares a purchase between the employers with a vacancy by vacancy, cuts it where
   any share would pass that employer's room, draws free cash down across markets, and names the payers on each lot
   (`BondedLot.payers`); `settle` charges those payers and nobody else, so people are not delivered unpaid and the goods
   lines keep their cash. The vacancy's wage line funds a part of a person (a person costs the present value of many years),
   so a short trade buys fewer people than before; free cash is the only other way to pay. Tests:
   `test_bonded_purchase_within_plan.py` (rules on built inputs). Measure: the people bought, printed per seed by
   (the test was removed from the suite), against the same command on the commit before.
9. On-the-job learning (`sim/economy/practice.py`, `Producer.crew_runs`): the producer's record keeps the runs its crew has made per
   trade; `practice.recipe_for` multiplies the recipe's booked hours by the curve's `unit_time_ratio` over the floor
   (`SOURCE_TASK_FLOOR_FRACTION`), so a first attempt needs the floor's inverse in hours and an established crew the booked hours;
   `plan` and `produce` use it. A trade with no entry is established (the opening's producers). The practice stays with the crew
   the producer stands for: growth in runs is hired hands who bring the recipe's mean practice and close `SKILL_GAP_CLOSED_PER_YEAR`
   of the gap to the crew's (Eurace Household_update_specific_skills), layoffs leave the stayers' practice (no forgetting), a new
   producer starts at the mean of the recipe's other producers or at a first attempt where there are none (Eurace's restarting
   firm takes the regional mean skill). Tests: `test_economy_practice.py`. Open: spoilage (`error_share`), a quit rate that
   removes practice apart from layoffs, entrants who join an existing producer's workshops, entry and hours-needed figures still
   use the booked hours, and the speed is the Eurace mix of skill levels, not a measured one (`retire`d to this complaint).
