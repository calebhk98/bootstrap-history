# The agent economy has one money per economy, so Mexica's cotton cloaks are an ordinary good

**Status:** open

Mexica used cacao beans for small payments and cotton cloaks (quachtli) for large ones. The agent economy carries one money per economy (`CurrencySpec`), so Mexica's money is cacao and cloaks are a good priced in beans (data note in `data/civilizations/mexica_1500.json`). Several moneys at once would also be needed for players with different currencies trading in one market.

What it would take: more than one currency per economy in the book and the markets, with an exchange market between them (`sim/economy/currency.py` has `exchange_rate` at metal parity as a start).

Design report: `Complaints/reports/agent-economy-several-moneys.md` (the assumption measured, three options, a step order with tests). It recommends per-area currencies first, then several media in one area.

Related: 382.
