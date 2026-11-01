# Rome opens in a low-employment state by construction, and employers' demand for labour cannot absorb the hours offered

**Status:** open - diagnosed on branch claude/labor-market-economy-stability-ueffy1; needs a design decision on how much of the society's labour goes through markets

**What is wrong.** On a fresh Rome opening stepped on the branch code, the people-based unemployment rate in wage trades
(`sim/economy/diagnostics.person_equivalent_unemployment`, printed by `spin-up-trace` as `people_unemployment`) starts
near a fifth and rises to about a half within ten years, and the share of offered hours that nobody hires
(`unsold_hours_share`) stays between a half and two thirds. Plausible pre-modern figures for people seeking wage work are a
few per cent to about a tenth. Real output now holds after the first year, so this is not the collapse fixed elsewhere
on the branch.

**What it is not** (each tested by ablation on a saved opened Rome economy; probes in the session scratchpad):

- Not the workers' ask floor: setting it to half or to zero lowers the wage and the price level but moves employment by a
  couple of points. Even at a zero wage employers bid for little more; nearly all idle hours sit in (trade, area) markets
  with no extra bid at any wage (Complaint 962).
- Not households failing to spend: rationed budget is now respent on the need's other goods within the year.
- Not productivity: hours per run by recipe do not change.
- Not the wage of displaced workers: idle workers reconsider their trade at the share that found no work; moving them to
  their plot or to other areas' trades changes the people rate by a few points and lowers output.

**What it is.** Employers' demand for labour covers well under half the hours offered, and the opening makes it so:

- The opening sizes producers to the final demand households' incomes pay for (`sim/economy/opening.py`), while every
  hour a household's plot and household work leave is offered to the market (`labour_supply.py`). Rome is nearly fed
  from its own plots, so most offered hours have no market use from the first year.
- Some sectors are sized for demand that does not last (muscle energy, coal, platinum, stone blocks: Complaint 961) and
  shrink back over a decade; nothing re-hires their people.
- Every reference model run on the branch (`Complaints/reports/labour-models-compared.md`) has one unit of labour per
  person, no home production, and an opening sized for (or calibrated to) near-full employment: Eurace sizes output so
  labour demand equals labour supply at the start, Caiani sets the unemployment rate as a calibration input.

**Why it matters.** Wages, prices and every producer's plans in a player's game sit on a labour market where most
people have no wage work, which is not a plausible Roman economy (CLAUDE.md 4.2).

**What it would take** (a decision for the owner first):

1. Decide how much of the society's labour goes through markets at the opening, from sources on the share of wage labour
   and the working year, rather than from what market demand happens to employ.
2. Then either size the opening so the people placed in wage trades are those the market employs and the rest farm their
   land (the plot trade's spare hours are then underemployment, not unemployment), or size market demand to employ the
   wage-labour share the sources give (more of what households consume is bought, less grown).
3. Count household work beside the working year, as the time-use sources do (question raised on the branch:
   `labour_supply.hours_kept_at_home` carves it out of the year).
4. Re-measure the people rate and the unsold-hours share over ten years on a fresh opening.

**Measure.** Step a saved opened Rome economy (`ROME_SPIN_UP_YEARS=3,2`) or run
`python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 15` and read `people_unemployment` and `unsold_hours_share`.
