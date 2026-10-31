"""`chained_ratio` and `next_chained_index` from written-out prices and quantities."""

QUICK_TOPIC = True

from .harness import check

from sim.markets.port_trace_chained import chained_ratio, next_chained_index

same = {"grain": 2.0, "cloth": 5.0}
check("equal prices give 1", chained_ratio(same, dict(same), {"grain": 10.0, "cloth": 3.0}) == 1.0)

ratio = chained_ratio({"grain": 2.0, "cloth": 5.0}, {"grain": 3.0, "cloth": 5.0}, {"grain": 10.0, "cloth": 2.0})
check("ratio is this year's prices over last year's at this year's quantities", abs(ratio - 40.0 / 30.0) < 1e-12, ratio)

ratio = chained_ratio({"grain": 2.0}, {"grain": 4.0, "iron": 9.0}, {"grain": 1.0, "iron": 5.0})
check("a good with no earlier price is left out", ratio == 2.0, ratio)

check("a good with no quantity is left out", chained_ratio({"grain": 2.0, "iron": 1.0}, {"grain": 4.0, "iron": 1.0}, {"grain": 0.0, "iron": 1.0}) == 1.0)
check("no common good gives None, not 0", chained_ratio({"a": 1.0}, {"b": 1.0}, {"a": 1.0, "b": 1.0}) is None)
check("the index multiplies the ratio", abs(next_chained_index(1.5, {"g": 2.0}, {"g": 3.0}, {"g": 1.0}) - 2.25) < 1e-12)
check("the index stays when there is no ratio", next_chained_index(1.5, {}, {"g": 3.0}, {"g": 1.0}) == 1.5)
