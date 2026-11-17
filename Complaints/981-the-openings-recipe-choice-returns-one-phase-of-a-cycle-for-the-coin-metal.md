# The opening's recipe choice returns one phase of a cycle for the coin metal, and an ore with no deposit is treated as unlimited

**Status:** open - found tracing England's falling money stock for Complaint 473 (Update 31); not fixed, because both fixes change which ores a civilisation has and need a decision (`Complaints/reports/473-owner-questions.md`, question 9)

**What is wrong.** Two things in how the opening chooses the recipes for a good, both seen on England's silver
(`PYTHONPATH=. python3 Complaints/reports/473-handoff/probes/coin_passes_probe.py england_1300` returns a different
answer for every other pass bound; `coin_runs_probe.py`, `coin_chain_probe.py` and `coin_opening_probe.py` beside it
show the recipes, their ceilings and what is placed):

- **`opening_runs.required_runs` does not converge and returns the last pass.** Silver is made three ways: as the
  co-product of smelting galena for lead, from jarosite ore with lead as the collector, and from silver ore. The lead
  recipe's main output at the opening's prices is its silver, so lead counts as a by-product and the recipes that use
  lead are held to the lead that silver-driven runs supply. The jarosite recipe is the cheapest and uses lead. Each pass
  reads the by-product supply and the required quantities of the pass before, and the passes alternate: one gives all
  the silver to jarosite, the next finds no lead for it and gives the silver to the lead recipe. The loop ends at its
  pass bound and returns one phase: jarosite smelters sized for all the silver, no runs of jarosite ore at all (the
  phase's required quantities held none), and lead sized for the other buyers of lead only, with galena and silver ore
  dug at their ceilings for the other phase's smelters. One more pass returns the other phase: the lead recipe at its
  ceiling, silver ore smelted, no jarosite smelter, and the jarosite ore dug for the smelters of the pass before. `fit_to_supply` then cuts
  the smelters to the lead there is. England opens with silver smelters in every tile and no mine for their ore; they
  smelt the stock they open with and then hire hands and make nothing (Complaint 473 Update 30).
- **A catalogue ore with no deposit on any of the economy's tiles runs anywhere.** `port_sites.site_limits` gives a
  recipe a limit only on tiles that hold a deposit of its ore, and `sites.is_sited` reads a recipe with no limit as
  unsited, so `UNSITED_EXTRACTION_ANYWHERE` lets it run on any tile with no ceiling. The module's own note says a tile
  whose deposits are worked out keeps a limit of nothing so the recipe does not fall back; an ore with no deposit at
  all falls back. England has no jarosite deposit (the catalogue's is Rio Tinto's), yet the opening prices jarosite
  ore, ranks the jarosite recipe first and has no ceiling on it. England's galena and silver ore, which do have
  deposits, are dug at their ceilings with no smelter sized to use them.

**Why it matters.** The coin's yearly loss is a demand the opening is meant to size a chain for
(`opening_metal.py`). With this choice England's mint strikes a small share of the loss from the first year, the money
stock falls every year and so do prices (Complaint 982, Complaint 473). Rome's opening has the jarosite deposit and
the same three recipes, so the same cycle is likely there (Complaint 961 notes lead short for its silver makers); not
measured.

**What it would take.**
- Make `required_runs` reach a fixed point where a by-product's users and its maker's main output feed each other
  (the consistent answer runs both recipes: the lead recipe as far as the silver the jarosite recipe cannot make, the
  jarosite recipe as far as that lead goes), or refuse loudly when the passes do not converge. A rule test with three
  small recipes of this shape shows it.
- Decide question 9: an ore the catalogue lists and no tile of the economy holds is absent (a limit of nothing on
  every tile), which is what the deposits say, and takes away ores the catalogue does not cover for a region
  (`unsited_probe.py mexica_1500`: Mexica's silver ore has no site and is dug anywhere today); or the fallback stays
  until the catalogue covers every region.
