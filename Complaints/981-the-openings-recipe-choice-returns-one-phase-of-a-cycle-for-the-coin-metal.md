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
- **Ores with no deposit are dug anywhere.** `port_sites.site_limits` limits a recipe that digs an ore to the tiles
  holding a deposit of the ore's resource. Two cases escape it, and `UNSITED_EXTRACTION_ANYWHERE` then lets the recipe
  run on any tile with no ceiling:
  - the jarosite ore recipe is tied to no deposit in any civilisation: the resource catalogue lists no resource whose
    ore good it is (`sim.geography.queries.ore_goods()`; the Rio Tinto deposit in the data is a silver deposit). So
    England's opening prices jarosite ore, ranks the jarosite recipe first and has no ceiling on it;
  - an ore the catalogue does list, with no deposit on the economy's tiles, has no limit either, although the module's
    own note says a worked-out tile keeps a limit of nothing so the recipe does not fall back.
    `unsited_probe.py <civ>` lists them with what is placed: England's gold, Norse's tin, galena and gold, Mexica's
    silver are dug this way today.
  England's galena and silver ore, which do have deposits, are dug at their ceilings with no smelter sized to use them.

**What a consistent choice does** (one England spin-up on a scratch copy with `silver_jarosite_kg` taken out of
`data/production/20_nonferrous.json`, `series_probe.py` beside the same run at the head): the choice settles on the
lead route and the silver-ore route at their ceilings, the placed chain is about the size of the coin's yearly loss,
silver is made every year at the mint's price, the money stock falls about a quarter as fast through the trimmed
stage and the price level about a third as fast, and output and hired hours are higher. It also shows what comes
next: the lead that comes with the silver has no buyers, its price goes to nothing and it piles up in the smelters'
stock, so producers' inventory value grows every year. A producer needs a way to be rid of a co-product nobody buys.

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
- Decide question 9: whether an ore with no deposit on the economy's tiles is absent (a limit of nothing on every
  tile, and the jarosite ore recipe tied to the jarosite deposit in the data), which is what the deposits say and
  takes away the ores listed above until deposits or trade supply them; or the fallback stays.
- A co-product nobody buys must not pile up for ever (free disposal, or a run sized on what all its outputs sell).
