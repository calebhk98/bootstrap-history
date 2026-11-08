"""The year's revenue assessments as one table (`assessment_kernels.py`) with the names kept beside its rows.

`AssessmentTable` is what `revenue.assess` answers and `world.revenue.revenue_assessments()` hands the year: the budget, the fiscal
response and the collection read its columns. It is also a read-only sequence of `revenue.Assessment` objects, made from a row when a
test, a screen or a mod asks, so nothing that reads one object at a time changes. `as_table` makes a table of a plain list of
`Assessment` (a test's or a mod's own answer) so the year has one path."""
from collections.abc import Sequence
from typing import Any, Iterator, List, Tuple

import numpy

from . import assessment_kernels as kernels
from .assessment_kernels import FORMS, PAYERS, RevenueForms, RevenuePayers


class FormRow:
    """What one form row needs beside its numbers: the names, and the payers' actors."""
    __slots__ = ("form", "basis", "material", "labour_to", "payers")

    def __init__(self, form: str, basis: str, material: str = "", labour_to: str = "", payers: Tuple[Any, ...] = ()) -> None:
        self.form, self.basis, self.material, self.labour_to, self.payers = form, basis, material, labour_to, payers


class AssessmentTable(Sequence):
    """The forms table, the payers table (rows in form order) and the names of both."""

    def __init__(self, rows: List[FormRow], forms: Any, payers: Any) -> None:
        self.rows, self.forms, self.payers = rows, forms, payers
        self.payer_actors = [actor for row in rows for actor in row.payers]

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, slice):
            return [self.assessment(row) for row in range(len(self))[index]]
        return self.assessment(range(len(self))[index])

    def __eq__(self, other: Any) -> bool:
        """Equal to a list of the same assessments (a caller that compared the old list keeps working)."""
        if isinstance(other, AssessmentTable):
            return list(self) == list(other)
        return isinstance(other, list) and list(self) == other

    __hash__ = None  # type: ignore[assignment]

    def number(self, row: int, column: str) -> Any:
        """A figure of the forms table as a Python float."""
        return float(getattr(self.forms, column)[row])

    def assessment(self, row: int) -> Any:
        """The `revenue.Assessment` a row stands for."""
        from .revenue import Assessment
        names, kind, number = self.rows[row], int(self.forms.kind[row]), self.number
        kept = number(row, "kept_by_officials")
        if kind == kernels.HELD_BY_PAYERS:
            first, count = int(self.forms.first_payer[row]), int(self.forms.payer_count[row])
            owed = tuple((names.payers[i], float(self.payers.owed[first + i])) for i in range(count))
            if count == 0:   # a sum over no payers is the integer 0
                return Assessment(names.form, names.basis, 0, number(row, "rate"), 0, payers=owed,
                                  collectible=number(row, "collectible"), concealed=0, kept_by_officials=kept)
            return Assessment(names.form, names.basis, number(row, "assessed_base"), number(row, "rate"), number(row, "money"),
                              payers=owed, collectible=number(row, "collectible"), concealed=number(row, "concealed"),
                              kept_by_officials=kept)
        if kind == kernels.LABOUR:
            return Assessment(names.form, names.basis, number(row, "assessed_base"), number(row, "rate"), number(row, "money"),
                              person_days=number(row, "person_days"), labour_to=names.labour_to, commute=number(row, "commute"))
        return Assessment(names.form, names.basis, number(row, "assessed_base"), number(row, "rate"), number(row, "money"),
                          number(row, "tonnes"), names.material, collectible=number(row, "collectible"), kept_by_officials=kept)

    def __iter__(self) -> Iterator[Any]:
        for row in range(len(self)):
            yield self.assessment(row)

    def money_of(self, row: int) -> Any:
        """The money a form yields (the integer 0 for a form on payers that named none, as the sum over no payers is)."""
        if int(self.forms.kind[row]) == kernels.HELD_BY_PAYERS and int(self.forms.payer_count[row]) == 0:
            return 0
        return self.number(row, "money")

    def total_money(self) -> Any:
        """The money of every form added as Python's `sum` adds them."""
        from sim.compiled_tables.sums import python_sum
        if not self.rows:
            return 0
        return float(python_sum(self.forms.money, len(self.rows)))

    def in_kind(self, row: int) -> bool:
        return bool(self.rows[row].material)

    def in_labour(self, row: int) -> bool:
        return bool(self.rows[row].labour_to)

    def has_payers(self, row: int) -> bool:
        return bool(self.rows[row].payers)


def build(rows: List[FormRow], form_figures: List[dict], payer_figures: List[dict], run_kernels: bool = True) -> AssessmentTable:
    """A table from the forms' input figures (a dict of column values per row) and the payers' (rows in form order). The kernel
    fills the outputs unless `run_kernels` is False (a table of finished assessments)."""
    forms = FORMS.new_table(RevenueForms, len(rows), len(rows))
    payers = PAYERS.new_table(RevenuePayers, len(payer_figures), len(payer_figures))
    for row, figures in enumerate(form_figures):
        for column, value in figures.items():
            getattr(forms, column)[row] = value
    for row, figures in enumerate(payer_figures):
        for column, value in figures.items():
            getattr(payers, column)[row] = value
    if run_kernels:
        kernels.assess_forms(forms, payers)
    return AssessmentTable(rows, forms, payers)


def as_table(assessments: Any) -> AssessmentTable:
    """The table itself, or a table of a list of finished `Assessment` objects (nothing is assessed again)."""
    if isinstance(assessments, AssessmentTable):
        return assessments
    rows, form_figures, payer_figures = [], [], []
    for assessed in assessments:
        first = len(payer_figures)
        kind = kernels.HELD_BY_PAYERS if assessed.payers else (kernels.LABOUR if assessed.in_labour else kernels.PLAIN)
        for _payer, owed in assessed.payers:
            payer_figures.append({"form": len(rows), "owed": owed})
        rows.append(FormRow(assessed.form, assessed.basis, assessed.material, assessed.labour_to,
                            tuple(payer for payer, _owed in assessed.payers)))
        form_figures.append({"kind": kind, "base": assessed.base, "assessed_base": assessed.base, "rate": assessed.rate,
                             "money": assessed.money, "tonnes": assessed.tonnes, "in_kind": 1 if assessed.in_kind else 0,
                             "collectible": assessed.collectible, "concealed": assessed.concealed,
                             "kept_by_officials": assessed.kept_by_officials, "person_days": assessed.person_days,
                             "commute": assessed.commute, "first_payer": first, "payer_count": len(payer_figures) - first})
    return build(rows, form_figures, payer_figures, run_kernels=False)


def group_numbers(names: List[str]) -> Tuple[List[str], Any]:
    """The distinct names in the order they first appear, and each name's number in that list."""
    order: dict = {}
    for name in names:
        order.setdefault(name, len(order))
    return list(order), numpy.array([order[name] for name in names], dtype=numpy.int64)


def accumulated(initial: List[float], group: Any, values: Any) -> Any:
    """`initial` with `values` added onto it by group, in row order, one add at a time."""
    totals = numpy.array(initial, dtype=numpy.float64)
    kernels.accumulate_by_group(totals, group, numpy.ascontiguousarray(values, dtype=numpy.float64), len(values))
    return totals
