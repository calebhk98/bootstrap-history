"""Notes waiting to be added to the ledger's tables, so a year's many small settlements, labour markets and rounds cost a few
kernel calls instead of thousands.

A caller that notes one settlement (or one labour result, one cleared round, one producer's output) at a time appends the rows to
plain lists here, which costs about what one dict update did. Before anything reads or writes a table the notes of its kind
feed, `flush` turns the lists into arrays and adds them in one call. The rows are in the order they were noted, so the sums and
the entry order are what noting them one by one gave. Four kinds, each writing its own tables:

    SETTLEMENTS  money_out, wages_in, sales_in, plant_spend, received, sold, imports_paid, exports_received
    HOURS        hours_hired, hours_hired_by_market, hours_sold
    ROUNDS       the clearing rounds and delivered
    OUTPUT       output

A read or write of one table flushes only its kind, so a producer reading its costs while another's output is noted does not
flush the settlements (`PENDING_KIND` in year_ledger_tables.py says which kind a table depends on)."""
import numpy

from .year_ledger_arrays import add_pair_amounts, note_hours_rows, note_round_rows, note_settlement_rows
from .year_ledger_tables import HOURS, OUTPUT, ROUNDS, SETTLEMENTS


def _floats(values) -> numpy.ndarray:
    return numpy.array(values, dtype=numpy.float64)


def _wholes(values) -> numpy.ndarray:
    return numpy.array(values, dtype=numpy.int64)


def _flags(values) -> numpy.ndarray:
    return numpy.array(values, dtype=numpy.bool_)


class PendingNotes:
    def __init__(self) -> None:
        self.counts = [0, 0, 0, 0]      # rows waiting, by kind
        self.settlements()
        self.hours()
        self.rounds()
        self.outputs()

    # ---- the lists of each kind (calling one empties it) ----------------------------------------------------------------------

    def settlements(self) -> None:
        self.agents, self.paid, self.received, self.imports, self.exports = [], [], [], [], []
        self.got_goods, self.goods_in, self.goods_out, self.purpose_kind, self.good = [], [], [], [], []
        self.template, self.reference, self.plant_bought = [], [], []
        self.counts[SETTLEMENTS] = 0

    def hours(self) -> None:
        self.fill_agents, self.fill_slot, self.fill_quantity, self.fill_price, self.fill_is_buy = [], [], [], [], []
        self.fill_trade, self.fill_market, self.fill_wage, self.fill_settled = [], [], [], []
        self.paid_by_slot, self.paid_to_slot = [], []
        self.counts[HOURS] = 0

    def rounds(self) -> None:
        self.round_market, self.round_quantity, self.round_price, self.round_moved = [], [], [], []
        self.counts[ROUNDS] = 0

    def outputs(self) -> None:
        self.output_agents, self.output_goods, self.output_quantity = [], [], []
        self.counts[OUTPUT] = 0

    # ---- into the tables ---------------------------------------------------------------------------------------------------

    def flush(self, tables, kind: int) -> None:
        """Add the waiting rows of one kind to the tables, in the order noted, and forget them."""
        if not self.counts[kind]:
            return
        if kind == SETTLEMENTS:
            note_settlement_rows(tables, tables.agent_numbers(self.agents), _floats(self.paid), _floats(self.received),
                                 _floats(self.imports), _floats(self.exports), _flags(self.got_goods), _floats(self.goods_in),
                                 _floats(self.goods_out), _wholes(self.purpose_kind), _wholes(self.good), _wholes(self.template),
                                 _wholes(self.reference), _flags(self.plant_bought))
            self.settlements()
        elif kind == HOURS:
            note_hours_rows(tables, tables.agent_numbers(self.fill_agents), _wholes(self.fill_slot), _floats(self.fill_quantity),
                            _floats(self.fill_price), _flags(self.fill_is_buy), _wholes(self.fill_trade), _wholes(self.fill_market),
                            _floats(self.fill_wage), _flags(self.fill_settled), _floats(self.paid_by_slot), _floats(self.paid_to_slot))
            self.hours()
        elif kind == ROUNDS:
            note_round_rows(tables, _wholes(self.round_market), _floats(self.round_quantity), _floats(self.round_price),
                            _floats(self.round_moved))
            self.rounds()
        else:
            add_pair_amounts(tables, "output", tables.agent_numbers(self.output_agents), tables.good_numbers(self.output_goods),
                             _floats(self.output_quantity))
            self.outputs()

    def flush_all(self, tables) -> None:
        for kind in (SETTLEMENTS, HOURS, ROUNDS, OUTPUT):
            self.flush(tables, kind)
