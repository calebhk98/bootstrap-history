# The engine quotes a trade's wage as an unweighted mean over tiles

**Status:** open

`AgentEconomy.answers` (`sim/engine/economy_port_year.py`) gives the engine each trade's wage as the plain mean of that trade's remembered wage on every tile, whether or not anyone works or is hired there. One thin tile can set the national figure: before the wage fixes in `sim/economy/labour_asks.py`, one Han tile's smith wage reached tens of thousands of labourer wages and made the quoted smith wage hundreds of times a labourer's. The fixes bound such tiles, but a mean that counts empty markets as much as busy ones still misstates what hiring costs.

Evidence: in a game at the opening, compare `game.labour_market.quote_annual("smith")` with the hours-weighted mean of `record.memory.wages` keys `smith|work@<tile>` over the year's labour results (`YearOutcome.wages` is already hours-weighted). No command prints this yet.

What it would take: quote `YearOutcome.wages` (weighted by hours hired), or weight by hours hired over recent years, in the port.

Related: 388, Complaints/reports/agent-economy-review.md.

## Economy side

`sim/economy/api.py` now publishes `wages_by_trade_weighted(economy)`: per trade, the remembered wage of each labour market weighted by last year's hours hired there (`EconomyRecord.hours_hired`, filled in `clear_labour` and saved with the record, so a resumed economy weights too). A trade that hired nowhere falls back to the unweighted mean. What remains is the port change in `sim/engine/economy_port_year.py`, `answers()`, which is outside `sim/economy`:

```diff
-sum(rows) / len(rows)
+api.wages_by_trade_weighted(economy)[trade]
```
