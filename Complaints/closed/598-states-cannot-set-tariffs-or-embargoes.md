# States cannot set tariffs or embargoes: customs has one rate and no partner

**Status:** closed. A state's tariff (a share of the goods' value at the source) and embargo on another country, set through `set_relation`, act in the markets: `landed_price` carries the tariff and an embargo removes the offer (`sim/engine/trade_duty.py`); the duty inside import payments reaches the treasury from the border (`sim/economy/tariffs.py`, `year_close.money_taxes`); the traders' route arithmetic carries the duty (`duty_between`, part of `freight_between`) and an embargoed crossing costs without limit, the duty paid to the destination's government actor at settlement; a partner's tariff and embargo on the home country cut the export bid. Offer caches key on the relations, so a mid-game change is seen at once. Test: `sim/tests/test_tariffs_and_embargoes.py`. Not done: a partner's own treasury in the legacy partner books receives nothing from the duty on our exports (the price falls by it); no quotas.

Part of Complaint 487 (No diplomacy).

Depends on 597.

**What is wrong.** A foreign state can shut its market to one smuggler and has an export policy for its monopolies. Nothing else: no tariff a state sets, no embargo, no quota.

**Evidence.** `landed_price` in `sim/engine/goods_market_offers.py` is the cross-border pricing point; `TaxForm` customs in `sim/economy/taxes.py` has one rate and no partner; `sim/agents/government_foreign.py`, `sim/agents/policy.py`.

**Why it matters.** Trade policy is how powers act on each other; without it a relation has no consequence.

**What it would take.** An embargo removes the offer, a tariff adds to the partner cost at `landed_price`, and the revenue reaches the setting government through the ledger. Price caches are invalidated when a relation changes mid-game.

**Test.** A test sets a tariff and an embargo between two countries: landed price rises by the tariff, an embargoed good has no cross-border offer, the setting government's ledger shows the revenue, and a mid-game change is seen without a stale price.
