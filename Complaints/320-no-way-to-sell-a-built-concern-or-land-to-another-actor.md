# There is no way to sell a built concern or farmland to another actor

**Status:** open

Complaint 265 asked for a lever out of the debt trap beyond selling stock, mothballing, closing and firing. Plant and land can only be bought (`buy farm`, building a concern), never sold, so capital sunk into them cannot be recovered when cash is short.

Decided against a one-sided `sell farm` in 265: a sale needs a buyer, so it belongs to the general-actor mechanism (a transfer of an asset from one actor to another at a price both sides compute from the same valuation: land value, plant replacement cost less wear, what the buyer's own output would earn from it). A founder-only command that pays a fixed share of the purchase price would hard-code an outcome (4.1) and could not serve firms, states or other players. Farmland is also being reworked under the land model, so the valuation should come from there.

What it would take: an asset-transfer function between two actors with a valuation both can compute, a `sell` target for farmland and for built concerns that uses it, the buyer paying from its own capital, and `cash_remedies.py` listing it with that same amount. Related: 265 (closed), 205.
