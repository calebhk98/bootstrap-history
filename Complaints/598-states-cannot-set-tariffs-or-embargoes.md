# States cannot set tariffs or embargoes: customs has one rate and no partner

**Status:** open

Part of Complaint 487 (No diplomacy).

Depends on 597.

**What is wrong.** A foreign state can shut its market to one smuggler and has an export policy for its monopolies. Nothing else: no tariff a state sets, no embargo, no quota.

**Evidence.** `landed_price` in `sim/engine/goods_market_offers.py` is the cross-border pricing point; `TaxForm` customs in `sim/economy/taxes.py` has one rate and no partner; `sim/agents/government_foreign.py`, `sim/agents/policy.py`.

**Why it matters.** Trade policy is how powers act on each other; without it a relation has no consequence.

**What it would take.** An embargo removes the offer, a tariff adds to the partner cost at `landed_price`, and the revenue reaches the setting government through the ledger. Price caches are invalidated when a relation changes mid-game.

**Test.** A test sets a tariff and an embargo between two countries: landed price rises by the tariff, an embargoed good has no cross-border offer, the setting government's ledger shows the revenue, and a mid-game change is seen without a stale price.
