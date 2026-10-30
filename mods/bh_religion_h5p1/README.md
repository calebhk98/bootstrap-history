# bh_religion_h5p1: religious institutions as economic actors

Adds a religious house as one more actor kind, `bh_religion_h5p1:religious_house`, and three civilisation
variants that start with one. No belief mechanics: a house is a landlord, a miller and a lender with a rule for its
surplus, competing with everyone else on the ordinary markets. Closes the design in
`Complaints/closed/269-religious-institutions-absent-as-economic-actors.md`.

## Turning it on

The shipped game is unchanged. A player picks one of the new civilisations at the new-game menu:

| Civilisation | Variant of | What the house is |
|---|---|---|
| `bh_religion_h5p1:england_monasteries` | `england_1300` | monastic houses: land, mills with a customary toll, a lending purse |
| `bh_religion_h5p1:rome_temple_estates` | `rome_100ad` | temple estates: land and a lending purse, no mills |
| `bh_religion_h5p1:han_monasteries` | `han_china_100ad` | the first Buddhist houses: a few hundred people, no mills |

The house needs the mod's Python: run `python3 sim/simulator.py mod-allow bh_religion_h5p1` once. Without consent
the civilisations still load but the house is not created (the cast entry waits for its kind).

## What it models

Each year a house (`hooks.py`, a subclass of the shipped church):

1. collects the rent of its endowed hectares at the land market's rent, a tithe when its entry sets one, and a
   milling toll (its share of the grain sold, times the toll rate);
2. pays its people a stipend at the going pay of a trade (`labourer`: a monk's keep, not a scribe's salary);
3. spends a declared share of what is left on land, at the capitalised rent (rent over the market rate), up to a
   ceiling, paying the landowners' edge through the ledger;
4. keeps the remainder in its purse, which is its lending stock: interest comes back through the purse book once the
   credit market offers the purse to borrowers (see limits).

All figures sit in the cast entry (`members`, `endowment_hectares`, and `plan`: `mill_share_of_grain`, `toll_rate`,
`milled_need`, `land_share_of_surplus`, `land_ceiling_hectares`). Each variant's entry carries `source` and
`confidence`; read them before trusting a number.

## Labelled heuristics

* `land_share_of_surplus` and `land_ceiling_hectares`: stand-ins until donors, the house's own rule and a land
  market with owners are modelled (land titles: Complaints/538; a house lending its purse: Complaints/closed/636).
* `mill_share_of_grain` (England): the share of milled grain that went through monastic mills is a guess of the
  right order; the toll rate (about a sixteenth) is the customary multure (Langdon 2004).
* Start sizes (`members`, `endowment_hectares`): placeholders of the right order, confidence D. They are added to
  the shipped `church:home` entry, which is left as it is.

## Known limits

* A house's purse is lent: the credit market offers the purse of every actor whose class sets `lends_from_purse`
  (`lender_offers`, `sim/finance/capital_market.py`), as it offers a firm's. The land market has no owners, so
  land a house buys does not leave the founder's market; land titles are `Complaints/538`.
* The three civilisations are `variant_of` patches (`mods/README.md`, Civilisations): each file names only its
  house, so a change to the shipped civilisation reaches the variant. A variant of Han is played without the shipped
  Han economy as a foreign partner.
* A house does not join the sector/grievance machinery (`sim/actors/world_groups.py` collects only the `church` and
  `academy` kinds), so the political risk of a dissolved house is not wired.
* Houses do not grow their headcount, take donations or found new houses.
