# A held-stock change could count the year's first change twice in the opening stock

**Status:** closed - fixed: `ChangeStock.legacy_snapshot_after_change` and its branch are deleted, so living stock takes the ledger's one path (`Ledger.change_stock`: snapshot first, then `rules.add_tonnes`). Test: `sim/tests/test_ledger_commands.py` `test_the_first_change_of_a_new_year_counts_once_in_the_opening_stock`. A baseline game's numbers change: the opening herds no longer count twice in year 0's opening stock.

`LivingStockYearlyMixin.change_stock` added the tonnes to the stock and only then read `_material_opening_stock()`,
which builds the year's opening snapshot from the current stock when the saved record is from an earlier year
(`material_throttle.year_opening_record`). On the first stock change of a year that snapshot already held the new
tonnes, and the method then added them to it again. The goods market's `_move_stock` did the same two steps in the
other order and was right. Two copies of one rule drifted apart: the coupling the module migration removes.

Both now send the ledger's `ChangeStock` (`sim/ledger/ledger.py`); the goods market's order is `sim/ledger/rules.py`
`add_tonnes` (tested in `sim/tests/test_ledger_rules.py`). The fix: delete the flag and its branch, so living stock
takes the same path, and record the changed opening stock in a regression test of the opening herd grant.
