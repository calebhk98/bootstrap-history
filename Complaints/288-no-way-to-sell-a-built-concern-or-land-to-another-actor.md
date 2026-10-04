# There is no way to sell a built concern or farmland to another actor

**Status:** partly - actors (firms, players) already sell a concern to another actor through exchange (`sim/agents/exchange.py`), both sides valuing it by the holder's recorded margin over the valuation horizon (`exchange_commands.concern_worth`); a buyer that needs a patent licence for the concern is refused. Not built: selling the founder's concern, and selling land back to the land market (both need the engine, below)

Complaint 261 asked for a lever out of the debt trap beyond selling stock, mothballing, closing and firing. Plant and land can only be bought (`buy farm`, building a concern), never sold, so capital sunk into them cannot be recovered when cash is short.

Decided against a one-sided `sell farm` in 261: a sale needs a buyer, so it belongs to the general-actor mechanism (a transfer of an asset from one actor to another at a price both sides compute from the same valuation: land value, plant replacement cost less wear, what the buyer's own output would earn from it). A founder-only command that pays a fixed share of the purchase price would hard-code an outcome (4.1) and could not serve firms, states or other players. Farmland is also being reworked under the land model, so the valuation should come from there.

What it would take: an asset-transfer function between two actors with a valuation both can compute, a `sell` target for farmland and for built concerns that uses it, the buyer paying from its own capital, and `cash_remedies.py` listing it with that same amount. Related: 261 (closed), 201.

Owner decision (2026-10-02): selling a concern can be lower priority. Land (farmland and other land bought) is a limited supply with a growth limit on arable land; it should sell straight back to the same land market it is bought from.

Update: concern sales between actors work through exchange (offer a `concern` for money or other things; acceptance re-checks both sides and moves nothing unless all holds). What remains needs engine folders:

- The founder's concern: the founder's household is not an `ActorRecord`, so it cannot be a party to an offer. The engine needs a `Household` adapter exposing `money`, `concerns`, `knows`, `record.stores` and `actor_id`, with `concern_ops.close_concern` and `open_concern` mapped onto `projects.operating`, `projects.opened_year` and the founder's size of the concern, and a `sell concern` command that makes an offer to an actor and a way for the actor to answer it.
- Land: owned by the engine land market, not an actor. The engine needs a `sell` on the land market that returns acres to the market's supply and pays the seller what the land model values it at (the same value `buy farm` uses, less nothing taken as a fee), keeping the cap on arable land, rather than an actor-to-actor transfer.
