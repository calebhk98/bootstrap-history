# Religious institutions do not exist as economic actors

**Status:** open

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md` (the review filed as 35), item 2 (religious upheaval).

## What is wrong

No civilisation has a religious institution that owns land, runs mills or lends money. The Han playthrough review points out that Buddhist monasteries became dominant landholders, mill owners and pawnshops between the first and fourth centuries, and that Daoist movements raised rebellions; the game has neither. Search `data/civilizations/` and `sim/engine/` for a religious actor: there is none.

## Why it matters

The point is not a theory of belief. Religious bodies are landlords, millers and lenders competing with the founder for land, labour and credit, and a source of political risk. Without them every society looks like a market plus a state, which misleads the player about who holds land and who can lend.

## What it would take

Model a religious body as one more actor kind (land, labour, a purse, a rule for what it does with surplus) on the actor model in `docs/architecture/ACTORS.md`, with data per civilisation saying which exist at the start date. No belief mechanics are needed for a first version. Related: 107 (independent firms), 114 (interest groups), 189 (actors that nothing reads).
