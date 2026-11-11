"""`goods_clear_kernel.clear_good_columns` against the chain of kernel calls it replaced (`goods_clear_chain_plain`), on seeded random
order tables with many ties: every output and every table it writes equal, and what it does when Python has to answer first."""
import unittest

import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.economy import goods_clear_kernel
from sim.tests import goods_clear_chain_plain as plain
from sim.tests.test_goods_good_kernels import copy_table, same

SEEDS = range(30)


def flat(found):
    """The arrays of a nested result in order (tuples opened, scalars made arrays)."""
    out = []
    for each in found:
        if isinstance(each, tuple):
            out.extend(flat(each))
        elif each is not None:
            out.append(numpy.asarray(each))
    return out


def table_rows(table):
    """A table's columns cut to its used rows, and its row count."""
    used = int(table.row_count[0])
    return [column[:used] for name, column in zip(table._fields, table) if name not in ("row_count", "capacity", "stock_slot")] + [numpy.array([used])]


def scratch_for(arguments):
    return (numpy.zeros(len(arguments[11]), dtype=numpy.bool_), numpy.zeros(len(arguments[8]), dtype=numpy.bool_), numpy.zeros(4, dtype=numpy.int64))


class ClearGoodColumnsIsTheChain(unittest.TestCase):

    def run_both(self, seed, good_id):
        tables, arguments = plain.random_world(seed)
        good_column = 1
        expected_tables = [copy_table(table) for table in tables]
        expected = plain.plain_clear_good(expected_tables, good_id, good_column, arguments)
        grown = [copy_table(table) for table in tables[:2]] + [reserve_rows(copy_table(table), 400) for table in tables[2:]]
        got = goods_clear_kernel.clear_good_columns(tuple(grown), good_id, good_column, *arguments, *scratch_for(arguments))
        return got, expected, grown, expected_tables

    def test_random_worlds_with_ties(self):
        batched = 0
        for seed in SEEDS:
            for good_id in range(plain.GOODS):
                got, expected, grown, expected_tables = self.run_both(seed, good_id)
                batched += len(got[3][1]) > 0
                same(self, flat(got[:3]), flat(expected[:3]))
                if expected[3] is not None:
                    same(self, flat(got[3:5]), flat(expected[3:5]))
                else:
                    self.assertEqual(len(got[3][1]), 0)
                same(self, flat(got[5:7]), flat(expected[5:7]))
                self.assertEqual(int(got[7]), expected[7])
                same(self, (got[8], got[9]), (expected[8], expected[9]))
                same(self, grown[0], expected_tables[0])
                same(self, grown[1], expected_tables[1])
                for found, wanted in zip(grown[2:], expected[10]):
                    same(self, table_rows(found), table_rows(wanted))
        self.assertGreater(batched, 20)

    def test_a_table_without_room_is_reported_and_no_row_is_written(self):
        reported = 0
        for seed in SEEDS:
            tables, arguments = plain.random_world(seed, 20, 20)
            before = [copy_table(table) for table in tables]
            scratch = scratch_for(arguments)
            try:
                goods_clear_kernel.clear_good_columns(tuple(tables), 0, 1, *arguments, *scratch)
            except goods_clear_kernel.NeedsInputs:
                reported += 1
                self.assertGreater(int(scratch[2].sum()), 0)
                for found, wanted in zip(tables, before):
                    same(self, table_rows(found), table_rows(wanted))        # (the offers' stock slots are written first: they are the same each time)
        self.assertGreater(reported, 5)

    def test_an_area_without_a_rate_and_a_tile_without_a_band_multiple_are_reported(self):
        for seed in SEEDS:
            tables, arguments = plain.random_world(seed, 20, 20)
            reserved = tables[:2] + [reserve_rows(table, 400) for table in tables[2:]]
            found = plain.plain_clear_good([copy_table(table) for table in reserved], 0, 1, arguments)
            if found[3] is None:
                continue
            arguments = list(arguments)
            area = int(arguments[0][0][found[3][1][0]])
            arguments[11] = arguments[11].copy()
            arguments[11][area] = False
            scratch = scratch_for(arguments)
            with self.assertRaises(goods_clear_kernel.NeedsInputs):
                goods_clear_kernel.clear_good_columns(tuple(copy_table(table) for table in reserved), 0, 1, *arguments, *scratch)
            self.assertEqual(numpy.flatnonzero(scratch[0]).tolist(), [area])
            arguments[11] = numpy.ones(len(arguments[11]), dtype=numpy.bool_)
            arguments[8] = numpy.full(len(arguments[8]), numpy.nan)
            with self.assertRaises(goods_clear_kernel.NeedsInputs):
                goods_clear_kernel.clear_good_columns(tuple(copy_table(table) for table in reserved), 0, 1, *arguments, *scratch)
            self.assertTrue(scratch[1].any())
            return
        self.fail("no seed batched a market")


if __name__ == "__main__":
    unittest.main()
