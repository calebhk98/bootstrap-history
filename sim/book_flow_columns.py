"""The year's goods flows read as one figure per good (a mixin of `Book`, sim/book.py): the columns a report wants, without a dictionary
per good."""
import math
from typing import List, Sequence

import numpy

from sim.book_purposes import REFERENCE_PREFIXES
from sim.book_types import GoodId


class BookFlowColumns:
    def flow_by_purpose(self, purpose: str, goods: Sequence[GoodId]) -> List[float]:
        """This year's quantity moved for exactly this purpose, for each good in order (0.0 for a good with no flow of it)."""
        found = self.purposes.find(purpose)
        by_number = numpy.zeros(len(self.good_ids) + 1)      # the last place stands for a good the book never saw (number -1)
        if found is not None:
            table = self.flow_rows.table
            rows = int(table.row_count[0])
            same = (table.purpose_code[:rows] == found[0]) & (table.purpose_reference[:rows] == found[1])
            by_number[table.good[:rows][same]] = table.quantity[:rows][same]
        return by_number[self.good_ids.numbers_of(goods)].tolist()

    def flow_by_prefix(self, prefix: str, goods: Sequence[GoodId]) -> List[float]:
        """This year's quantity moved for any purpose that starts with `prefix` (one of the book's reference prefixes), summed exactly,
        for each good in order."""
        if prefix not in REFERENCE_PREFIXES:
            raise ValueError("%r is not a purpose prefix the book splits at" % prefix)
        template = self.purposes.templates.find(prefix)
        by_number = numpy.zeros(len(self.good_ids) + 1)
        if template is not None:
            table = self.flow_rows.table
            rows = int(table.row_count[0])
            same = table.purpose_code[:rows] == template
            order = numpy.argsort(table.good[:rows][same], kind="stable")
            held, quantities = table.good[:rows][same][order], table.quantity[:rows][same][order]
            starts = numpy.flatnonzero(numpy.diff(held)) + 1 if len(held) else numpy.zeros(0, dtype=numpy.int64)
            for group, numbers in zip(numpy.split(quantities, starts), numpy.split(held, starts)):
                if len(group):
                    by_number[numbers[0]] = math.fsum(group.tolist())
        return by_number[self.good_ids.numbers_of(goods)].tolist()
