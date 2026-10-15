# Most non-Roman ore districts have no size, so they name no site

**Status:** open

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
