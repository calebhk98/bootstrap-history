# The agent economy with several moneys

Design report for Complaint 392. No code changed. Counts were taken with `grep -n` over `sim/economy/` at the commit this report was written on; re-run the commands in the last section before acting.

## The assumption, measured

The ledger is already multi-currency; the economy above it is not. The book (`accounts.py`) keeps purses per `(agent, currency)`, `Transfer`, `Loan`, `LoanRequest`, `ClearingResult` and `Fill` carry a currency, and `MarketMemory` holds `rates`, `price_levels` and `expected_inflation` keyed by currency. What is single is the choice of currency: it is named once, in the setup and the record, and read back from there.

About 65 sites in `sim/economy/` (plus 5 in `sim/engine/economy_port*.py`) read that single choice:

| Form | Sites | Where (main ones) |
|---|---|---|
| `setup.currency_id` | 37, in 18 files | `economy.py:80,91,217,223,269,324`; `year_goods.py:40,79,94,141,211,225`; `year_close.py:24,42,81,169,176`; `year_labour.py:90`; `entry_year.py:35,95,121`; `lending.py:42,59`; `opening.py:71,72,256`; `state_budget.py:41,77`; `land_market.py:179`; `notional.py:52`; `api.py:61,71,76,81` |
| `record.currency` (one `CurrencySpec`) | 14 | `mint.py:34,49,69,84,106`; `money_audit.py:58`; `state_finance.py:58,59,62,65,67,68`; `year_close.py:76,77` |
| `view.currency_of(area)` callers | 5 | `entry.py:126`; `households_close.py:53`; `households_orders.py:101`; `producers.py:203`; `producers_close.py:68` |
| The one-currency fields and fallbacks | 8 | `setup.py:36,71`; `record.py:23,45,69`; `opening.py:54`; `market_memory.py:86,106` |

Three of these matter more than their count:

1. `MarketView.currency_of(area)` (`market_memory.py:105`, `protocols.py:61`) looks like the hook for several moneys, but nothing ever writes `currency_of_area` (`market_memory.py:45`), so it always returns the setup's currency. Its five callers already ask the right question (which money does this area price in); everything else just does not ask.
2. Markets are keyed `(good, area)` and an order carries no currency. `year_goods.py:141` and `year_labour.py:90` stamp the one currency on the clearing result, and `settlement.py:37,43` pays in it. A market therefore has exactly one money.
3. The mint, the metal audit and the state's finance take one `CurrencySpec`: `mint.py` reconciles one coin against one metal, and `money_audit._metal_gap` returns a gap for one currency. Foreign trade (`foreign.py:66`, `api.py:71`) reads `edge:external` in one currency; partners already settle in "the partners' coin ledgers", so foreign money exists in the book only as a flow through the edge.

Already generic, needing no change: `credit.py` matches requests to offers by currency (`credit.py:70,72`), `credit_claims.py` filters by currency, `metal_stock.yearly_wear` takes a spec, `currency.exchange_rate` gives the parity of two metal-backed specs, `producer_exit.py` repays loans in each loan's own currency.

## Options

**(a) One unit of account, several media held as goods at mint parities.** Prices, wages, rates and the price level stay in one numeraire. Cacao, cloaks, gold coin and silver coin become money-goods or coin purses whose value in the numeraire is their parity (a coin's metal weight times the metal's price) and which the buyer's order settles in from whatever it holds.
- Cost: low to medium. Markets stay single-currency; the change is in settlement (pay from a mix of purses, valued at parity) and in the cash balance (a household's cash is the sum of purses at parity). `mint.py` and the audit become per-spec loops.
- Risk: the parity is an input, which comes close to hardcoding an outcome (4.1) unless it is derived from the metal's market price; a commodity such as a cloak has a floating value, so a fixed parity is wrong for it. It cannot represent a player's currency whose value is not the numeraire's.
- Unlocks: Gresham's law and bimetallic flows. With a fixed mint ratio and a market ratio that moves, the cheaper-in-market metal circulates and the other is hoarded or melted and exported (`economy-research-extraction-and-money-metals.md`, item 4). Mexica cacao and cloaks fit if cloaks may be held as money at a derived value. It does not unlock players' currencies.

**(b) Markets quoted per currency with exchange markets between currencies; money changers as agents.** Each good's market clears in one or more currencies; a currency pair has its own market where changers hold both purses and quote a rate.
- Cost: high. Market keys and memory (`prices`, `wages`, last price) gain a currency; every consumer of price memory changes; the exchange market needs changers with inventory, risk and arbitrage limits, plus a rule for which currency an order is made in.
- Risk: the largest; two-sided price memory doubles the stale-price problem, and exchange rates could diverge from metal parity with no anchor before changers exist.
- Unlocks: everything in (a) as an outcome rather than an input (the parity emerges from changers arbitraging metal), floating rates between players and fiat issuers, price-specie flow between currencies.

**(c) Per-area currency only.** Each area (a country's territory) prices and settles in one currency, using the dormant `currency_of_area` map; a cross-area trade is paid in the seller's currency by an exchange at the border, using `exchange_rate` (parity for coin, a rate for fiat).
- Cost: medium and small steps. Replace the 37 `setup.currency_id` reads with per-area lookups, and make `record.currency` a map of specs by currency id. Markets remain single-currency.
- Risk: a market spanning two areas, and a good priced in one area but bought with another's money, need the border exchange to be real or a fudge appears.
- Unlocks: players' own currencies and other countries as players, debasement and fiat by an issuer per country. It does not give Mexica (two moneys in one area) or bimetallism.

## Recommended order

Take (c) first as the foundation, then (a) for in-area plurality; leave (b) until players trade enough to need real exchange markets. (c) removes the single-currency reads, which both of the others need.

1. **Name the currency per area.** Make `currency_of(area)` the only reader of the setup's currency; add `currency_of_area` to the setup and fill it from the civilisation. Test: a two-area setup where an area is given another currency id and `view.currency_of` returns it; single-currency runs unchanged under `python3 -m sim.tests.fingerprint`.
2. **Replace `setup.currency_id` in year steps** with the area's currency (`year_goods`, `year_labour`, `year_close`, `entry_year`, `lending`, `state_budget`, `land_market`, `notional`), one file group per agent. Test: a two-area economy clears each market in its area's money and `money_audit` residual is zero in both.
3. **Make `record.currency` a map** and loop `mint`, `money_audit._metal_gap`, `metal_stock.yearly_wear` and `state_finance` over it. Test: two struck-coin currencies, each with its own mint stock, each audit gap zero.
4. **Per-currency rates, price levels and wage memory** in the opening spin-up (`opening.py:71`). Test: spin-up settles an interest rate per currency; the single-currency fingerprint is unchanged.
5. **Border exchange.** Trade across areas settles via an exchange agent holding both purses at `exchange_rate` plus a margin. Test: money conserved per currency; the changer's two purses net to its margin.
6. **Several media in one area (option a).** A household's cash is the sum of its purses at derived parity; settlement draws from the purses by a stated rule. Test: with a mint ratio away from the market ratio, the over-valued metal accumulates and the other leaves (Gresham), without a scripted flow. Then give Mexica cacao and cloaks.
7. **Floating exchange markets (option b)** only after 5 and 6, with changers who may profit or lose. Test: an exchange rate that departs from parity brings arbitrage back.

## What stays invariant

- Money is conserved per currency: `money_audit` residuals are zero for each currency, not for a sum. A transfer names one currency and nets to zero across the payer and payee; an exchange is two transfers in two currencies.
- Money and goods enter or leave only through named edge accounts. Each currency gets its own `EDGE_ISSUE`, `EDGE_WEAR`, `EDGE_MINT` and `EDGE_EXTERNAL` records (the book already tracks edges by currency); `edge:legacy` volume stays measured and falling.
- Metal embodied in coin equals the mint's metal stock plus awaited wear, per spec.
- No content ids in the engine (4.7): which currencies exist and which areas use them are data.
- Save and load round-trip within a build; no migration (4.6).

Counts: `grep -n "setup.currency_id" sim/economy/*.py | wc -l`; `grep -n "record.currency\b" sim/economy/*.py | wc -l`; `grep -n "currency_of" sim/economy/*.py`.
