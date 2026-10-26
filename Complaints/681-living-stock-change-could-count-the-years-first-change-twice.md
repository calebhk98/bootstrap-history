# A held-stock change could count the year's first change twice in the opening stock

**Status:** fixed on `sim-module-registry-plan` (the ledger's `ChangeStock`); closes with that branch

`LivingStockYearlyMixin.change_stock` added the tonnes to the stock and only then read `_material_opening_stock()`,
which builds the year's opening snapshot from the current stock when the saved record is from an earlier year
(`material_throttle.year_opening_record`). On the first stock change of a year that snapshot already held the new
tonnes, and the method then added them to it again. The goods market's `_move_stock` did the same two steps in the
other order and was right. Two copies of one rule drifted apart: the coupling the module migration removes.

Both now send the ledger's `ChangeStock` (`sim/ledger/ledger.py`), which takes the snapshot first and applies
`sim/ledger/rules.py` `add_tonnes` once. Whether the double count ever fired in a shipped scenario is what the
equivalence check of that commit answers (`docs/architecture/MODULE_MIGRATION_TASKS.md`, the ledger prototype).
Regression test: `sim/tests/test_ledger_rules.py`.
