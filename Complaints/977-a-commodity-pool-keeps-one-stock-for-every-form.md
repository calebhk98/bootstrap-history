# A commodity pool keeps one stock for every form, so bar and ore held by a seat are one number

**Status:** open - found closing Complaint 576

**What is wrong now.** A seat's material ledger keeps one counter per commodity (`data/world/commodities.json`: the `iron`
pool's `material_keys` are bar, ore, bloom, sheet and cast iron). Since 576 a sale from the pool is priced and cleared as the
form its mines raise (`raised_material`, `sim/prices/rules.py` `sold_material`), so mined ore no longer sells at the bar price.
But the counter cannot tell a tonne of ore from a tonne of bar, so bar iron the seat bought also sells as ore, at a fraction
of what it paid; and a project bill or input drawn from the pool counts mined ore as if it were bar.

**Why it matters.** A tonne of ore and a tonne of bar are different goods (CLAUDE.md 4.3: interventions propagate through
normal rules). The 576 fix chose the form that cannot be sold above its making cost; it does not make the ledger right.

**What it would take.** Keep the seat's stock by material key (ore, bar, bloom...) and resolve the pool only where a reader
genuinely wants "any iron" (throttle banking, project bills that accept any form, the demand and supply tags), with the
conversion between forms done by the recipes that exist (smelting, forging). Readers of the pool: grep `material_keys`,
`price_material`, `priced_key` and `own_material_supply`.

**Test.** A seat holding bar it bought and ore it mined sells each at its own good's price; a bill for bar is not met by ore.
