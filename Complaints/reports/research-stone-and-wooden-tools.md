# Research: stone and wooden tool figures (Complaints 650 and 659)

Only text opened in the session is quoted. Where a search summary named a figure but the source was not opened, it is not used.

## Sourced

- **Wooden against iron tools, hours factor** (`data/world/trades.json`, farmer `tool_hours_factor`). Shukurov, Videiko, Sarson, Davison, Shiel, Dolukhanov, Pashkevich, "Productivity of pre-modern agriculture in the Cucuteni-Trypillia area" (arXiv 1505.05121, PDF read), reporting Semyonov 1974 pp. 194-226: an oak dibble tilled "st = 5 m2/person-hour on a dense, half-virgin soil"; "Adding an iron point to an oak dibble increased the productivity to st = 6-8 m2/person-hour on virgin soil". Factor = 7 / 5 = 1.4 (range 1.2 to 1.6), replacing 1.5. Caveat: a pointed dibble, not a hoe or spade; the soils are described differently. Test: `sim/tests/test_tool_hours_sourced.py`.

## Read, but only a bound or context (no data figure changed)

- Blade life: Hester, Spencer, Busby and Bard, "Butchering a Deer with Obsidian Tools" (Berkeley ARF, https://digitalassets.lib.berkeley.edu/anthpubs/ucb/proof/pdfs/arf033-04.pdf): one flake "was used for over 30 minutes in cutting tasks, only very minor wear resulted and the tool was still serviceable at the conclusion of the experiment". A lower bound only; no end of life; the 0.05 effectiveness of `obsidian_blade_kg` stays a labelled heuristic.
- Stone against steel felling, context for the knapper's `stone` tool basket: Museum of Stone Tools page on New Guinea (https://stonetoolsmuseum.com/new-research/using-stone-axes-and-adzes-insights-from-new-guinea/): "Compared to steel axes, felling small trees with stone axes took from 2-2.5 times longer. This increased to 4-4.5 times longer for large trees." A secondary summary of Petrequin and Petrequin; the trade has no hours factor for stone today, so nothing in the data uses it yet.
- Putz, Fletcher and Magee, Forests 14, 202 (2023, PDF read): for an experienced chopper, stone needs "an additional 4.25 min and 150 strokes" to fell an un-tensioned 5 cm tree; it reports more than a dozen earlier experiments that "consistently report that much more time and energy are required to fell trees with stone than with bronze, iron, or steel axes". An absolute difference, not a ratio.
- Clark, "Prismatic Blademaking, Craftsmanship, and Production", Ancient Mesoamerica 8 (abstract read): output at Ojo de Agua "26,000, or fewer, fine blades per year" as part-time work over three months. No hours per blade, so `obsidian_blade_kg` labour stays a heuristic.

## No source found (kept as labelled heuristics with `retire`)

Hours per tonne of obsidian or flint quarried; hours per kilogram of blades (including the mass lost preforming nodules); finished flint tool mass per kilogram of flint and knapping hours; knapper training years; blade and flint tool effectiveness against bronze; wooden tool service life; wood and carpenter hours per tonne of wooden tools; the by-hand hours factor; wooden tool stock per worker.

Leads not opened (search summaries only, so not cited as figures): the Ramat Tamar flint quarrying experiment (Neolithic Ramat Tamar, Israel), which a search summary said reports blocks excavated per worker per day; Clark 1982 and 1984 (Lithic Technology 13); Titmus and Woods; Madsen's Lejre flint axe grinding experiments (tidsskrift.dk/jda/article/view/126138, full text not read); Mathieu and Meyer 1997, Journal of Field Archaeology 24 (paywalled; the Penn Museum account gives only "markedly faster using metal axes").
