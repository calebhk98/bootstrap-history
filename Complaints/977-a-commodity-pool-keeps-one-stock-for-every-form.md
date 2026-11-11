# A commodity pool keeps one stock for every form, so bar and ore held by a seat are one number

**Status:** open - mapped, not contained; staged plan below (stage 1 not started)

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

## Map (read and written; measured by grep, no numbers kept here)

The ledger is `StockLedger` in `sim/ledger/` (`material_stock_ledger`, keyed by the pool's commodity id, e.g. `iron`; the same dict
also holds living stock and other non-material keys). Its commands are `ChangeStock`, `BankStock`, `DrawDownStock`
(`sim/ledger/ledger.py`: `change_stock`, `bank_stock`, `draw_down_stock`); views `goods_stock`, `held_goods`, `goods_stock_opening`.
The pool is `materials.material_pool(material) -> (commodity, tag)` (`sim/materials/supply.py`, `rules.tag_of`, the table
`MATERIAL_CHECKS` in `sim/materials/constants.py`, where bar and ore share `("iron", "mine:iron")`).

Writers of stock:
- `sim/markets/port_goods_orders.py` (`ChangeStock(order["stock_key"], ...)` on a sale post and on settlement of a buy or an unsold remainder);
  the `stock_key` is made in `sim/materials/project_bill.py` (`post_project_orders`, `reorder_project_materials`) as `material_pool(material)[0]`.
- `sim/materials/throttle.py` (`BankStock(reading.banked)`: the unused owned flow of each pool is banked by commodity).
- `sim/living_stock/holding.py`, `trading.py` (`ChangeStock(commodity_of(material), ...)` for herds).
- `sim/coin/theft.py` (`DrawDownStock`).
- `sim/engine/seat_handover_empty.py` (reset), `sim/engine/invariants.py` (reads the raw dict).

Readers of stock: `sim/materials/` (`throttle.py` opening stock per commodity; `availability.py`; `project_bill.py` +
`rules.material_bill` `stock_of(commodity)`; `supply.py` `material_supply_route`, `materials_report`), `sim/projects/researcher.py`,
`sim/sharing/module.py`, `sim/markets/port_world_reads.py` (`stock_t`), `sim/finance/cash_remedies.py` (sells every held key, so it
already iterates keys), `sim/living_stock/holding.py`, `sim/resources/remedies.py` (saltpetre), `sim/engine/ui_port.py`, the market and
materials screens. Many test files read `goods_stock[commodity]` or send `ChangeStock`.

## Why it is not a contained change

1. The pool (commodity, tag) is the unit of the whole materials module, not just of the stock: demand is grouped by it, the throttle
   draws and banks one figure per pool against one yearly own-supply flow (`mine:iron`) and one market headroom, project bills meet a
   need from stock, then the pool's own flow, then the market. Splitting only the stock leaves the bill meeting a bar need from the
   iron mine's ore flow (`from_own`), so "a bill for bar is not met by ore" needs the flow side split too.
2. Which form the throttle banks (the mine raises ore: `raised_material`) and which form a draw takes from the bank has no rule yet;
   the conversion between forms (smelting, forging recipes) is not wired into the bill or the throttle.
3. The same dict keys non-material stock (living stock, capacity keys swept into `capacity_pool`), so keys must stay unambiguous.
4. Writers and readers span well over fifteen files across seven modules (ledger, materials, markets, living_stock, coin, finance,
   projects, sharing, resources, engine, ui) and a large share of the test files, each reader needing the "this form" or "any form"
   decision; the throttle and bill are the hard ones.

## Staged plan

1. Add a ledger view `held_by_form` and a pure rule `pool_total(stock_by_form, pool_members)`; make every "any form" reader (throttle
   opening stock, `availability`, `material_supply_route`, `researcher`, `sharing`, `materials_report`, `cash_remedies`) call the pool
   total, so behaviour is unchanged. Test: the rule sums bar and ore.
2. Switch the writers to material keys: `stock_key` becomes the material bought or sold; living stock and `theft` keep their keys;
   `BankStock` banks the raised form. Save/load round-trips (no migration, 4.6). Test: `ChangeStock` of bar and ore leaves two entries.
3. Make the project bill and a draw "this form": stock of the needed material first, then the pool's flow only for the form it
   yields, then the market; a missing form is bought or made by an existing recipe, never converted silently.
4. Make `sold_material` return the form held (revisit the 576 rule), so bar sells as bar and ore as ore; delete `raised_material`
   as the sale form (it stays the form the mine banks).
5. Close with the regression tests named in "Test" above, then a whole-game re-measure by the orchestrator.
