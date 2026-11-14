# A deposit's output is a share of Rome's 100 AD output, so supply is fixed at Rome's technology

**Status:** open

Every named deposit carries `share_of_empire_output` or `share_of_reference_output` (data/world/geography/deposits/*.json;
constants `DEPOSIT_SHARE_*` in `sim/world/deposits.py` and `DEPOSIT_REFERENCE_SHARE_*` in `sim/geography/mineral_shares.py`).
`load_deposits` turns the share into `quantity_tonnes_per_year` by multiplying it by `empire_output_100ad` in
data/world/resources.json, and `Geography.mineral_scale` gives a civilisation the summed share of the deposits on its tiles.
So what a mine can raise is a fraction of what Rome raised in 100 AD with Roman methods. A player with modern mining
technology, or any later date, still draws a Roman share: this is a historical outcome used as an input (CLAUDE.md 4.1).

Found sourcing the shares (Pass 11). Sourced output figures for districts come from different dates (Falun's 1650 peak,
Upper Mississippi's 1847 peak, Cobalt's 1911 peak, Sala's lifetime average), so a "share of Rome's output" built from
them mixes technologies: Cobalt silver comes to 4.25 times Rome's whole silver output, and the industrial coal fields
hundreds of times Rome's coal. No single rule makes those figures comparable, so the shares were not changed; the
sourcing branch (`mineral-share-sources`) is kept unmerged.

**What it would take.** Describe each deposit by what is physically in the ground, in one unit for every row: contained
metal in tonnes (cumulative recorded production plus remaining reserves, or the resource estimate), with its ore grade
and depth, which most deposits already carry. Output then follows from the labour, technology and capital applied to
that stock (the extraction-cost curve in `sim/world/deposits.py` already prices depth, grade and hardness), and the
civilisation's share of a resource on its tiles follows from contained metal, not from a Roman output figure.
`empire_output_100ad` stays only as a validation target for the Rome baseline (DESIGN 4.2), never as an input.

**Research needed.** Contained metal (cumulative production plus reserves, tonnes, with the source and year) for every
named deposit row.

**Research done (2026-11).** Most deposit rows now carry `contained_tonnes`, `contained_basis` and `contained_source`
(the basis says when a figure is a lower bound, a stand-in mine for a generic regional row, a resource rather than a
reserve, or a country-level figure used for one row). Count the rows still without it with
`grep -L` over the rows, or `python3 -c` on data/world/geography/deposits/*.json for rows lacking the key. The rows left
empty are mostly generic regional rows, gems, Stassfurt and Hallstatt salt, and the three saltpetre districts, which are
a regenerating soil flow and need a decision on what stock to enter. The fields are data only: no code reads them yet.
