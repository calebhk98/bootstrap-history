# Most non-Roman ore districts have no size, so they name no site

**Status:** closed

A deposit names a site (a limit on an ore recipe's runs on its tile) only when the catalogue gives it an
endowment, or the older deposit model sizes it from `share_of_empire_output` (Roman-world rows only)
(`sim/engine/mine_deposits.py`, `_deposit_base`). Every row of `reference_output_sites.json` and the new gold and
mercury rows of `ancient.json` carry neither, so a Chinese, Indian, Mexican or Scandinavian ore recipe has no
site limit except from hidden deposits the seat prospects, and runs where the economy's fallback
(`UNSITED_EXTRACTION_ANYWHERE`) lets it. Measure: `python3 -c` over `sim.geography.api.worked_deposits` for a
held tile set, counting rows with `size_tonnes` None.

A second gap sits in the same path: `mined_before` caps a working at the years a deposit takes to work out at the
`resources_working_share_per_year` rate, so any dated deposit first worked longer ago than that is already worked
out at the start (no room), however large its endowment. Check which dated deposits that closes for a Rome start
before dating more rows.

What it would take: a defensible endowment and ore grade for each district, from the production series in the
archaeometallurgy literature (the Tonglushan slag heap gives a production, not a remaining resource), and a decision
on whether the working-out cap should bound a deposit that was worked at a fraction of the rate.

## Resolution

- A named district with no endowment now takes the geological model's expected size
  (`sim/geography/resources_district.py`, reached through `worked_deposits` and `mined_before`): the closed-form mean
  of the tonnage (and grade) lognormal of its own `deposit_type` where the mineral defines that type, else the mean
  over the mineral's types weighted by their deposit counts, truncated at `resources_tonnage_truncation_sigmas` and
  bounded by the tile's crustal ceiling (area, depth, crust density, ore fraction). Each row says where its size
  came from in `size_basis`; no figure is stored per district. A row carrying `share_of_empire_output` is still
  sized by the engine's output model. Measure: `worked_deposits` over a held tile set, rows with `size_tonnes` None.
- The working-out cap is gone. A deposit yields a fixed share of what it still holds each year since it was first
  worked, so it empties by an exponential and no horizon closes it. The share is the deposit's historical rate over
  its size where the data gives the rate (`sim/engine/deposit_history.py`: share of the reference empire's output
  times its output), else `resources_working_share_per_year`. Cyprus copper stays closed at a Rome start because its
  data say so (the rate it is rated at, over three thousand years, against an endowment the entry itself calls the
  copper smelted in antiquity); Rio Tinto copper, which the cap closed, keeps a small remainder. The rate is the
  reference-date rate held constant since the first working, which overstates early output; a series per deposit
  would replace it.
- `first_worked` no longer needs an endowment (`test_deposit_workings_stated`: a precious deposit states a date or
  why it is unknown; a size comes from the model). Sala (lead and silver) is dated to the start of the fifteenth
  century from its own source ("worked from the fifteenth century at the latest"), so the Norse at 900 no longer
  get Swedish lead and silver; they declare both in `imported_ores`. Taxco silver is dated to about 1532 from its
  own source, so the Mexica at 1500 declare silver imported. Scania coal is dated from its own source (late
  eighteenth century), so a Rome start does not mine it.
- Undated rows in the reference file whose sources do not give a start (for example Rammelsberg lead, which sits in
  Rome's and England's tiles) are still taken as known from the beginning; they need a dated source before they
  are dated.
- Complaint 519: see the note there. Rome's iron ore stays far above its cost, so it stays open.
