"""The ledger's notes of money and goods moved outside a settlement: postings, summed sales, payments in no market, plant purchases.
They turn names to numbers and add whole arrays through `year_ledger_arrays.py`; `YearLedger` mixes them in."""
from typing import Dict, Iterable, List, Tuple

import numpy

from . import year_ledger_arrays as arrays
from .types import AgentId, EDGE_MINT, GoodId, GoodsMove, Transfer, is_external_edge
from .year_ledger_tables import SETTLEMENTS

SALE_PREFIX = "sale of "    # settlement's purpose for a goods sale


def _floats(values) -> numpy.ndarray:
    return numpy.asarray(values, dtype=numpy.float64)


class PostingNotes:
    """Methods of `YearLedger` that note postings (they use its `tables`, `import_accounts`, `export_accounts`, `plant_spend` and
    `pending_mint_takes`)."""

    def add_income(self, wages: bool, agents, amounts) -> None:
        self.tables.flush(SETTLEMENTS)
        arrays.add_income(self.tables, wages, agents, amounts)

    def note_postings(self, postings: Iterable[object], purpose_kind: str = "") -> None:
        tables = self.tables
        postings = list(postings)
        transfers = [posting for posting in postings if isinstance(posting, Transfer)]
        moves = [posting for posting in postings if isinstance(posting, GoodsMove)] if purpose_kind == "sales" else []
        if transfers:
            amounts = _floats([each.amount for each in transfers])
            self.add_money_out(tables.agent_numbers([each.payer for each in transfers]), amounts)
            if purpose_kind in ("wages", "sales"):
                self.add_income(purpose_kind == "wages", tables.agent_numbers([each.payee for each in transfers]), amounts)
            self._note_foreign(transfers)
        if moves:
            quantities = _floats([each.quantity for each in moves])
            goods = tables.good_numbers([each.good for each in moves])
            self.add_pair_amounts("received", tables.agent_numbers([each.receiver for each in moves]), goods, quantities)
            self.add_pair_amounts("sold", tables.agent_numbers([each.giver for each in moves]), goods, quantities)
            for move in moves:
                if move.receiver == EDGE_MINT:
                    taken = (move.giver, move.tile)
                    self.pending_mint_takes[taken] = self.pending_mint_takes.get(taken, 0.0) + move.quantity

    def _note_foreign(self, transfers: List[Transfer]) -> None:
        """Money across the border, by the domestic party and the good named in the purpose: paid to a foreign edge,
        received from one, taken for a landed cargo's sale, or paid for a cargo bound abroad."""
        imports, exports = ([], [], [], []), ([], [], [], [])
        for transfer in transfers:
            sale = transfer.purpose.startswith(SALE_PREFIX)
            if is_external_edge(transfer.payee) and not is_external_edge(transfer.payer):
                side, party = imports, transfer.payer
            elif is_external_edge(transfer.payer) and not is_external_edge(transfer.payee):
                side, party = exports, transfer.payee
            elif transfer.payee in self.import_accounts and sale:
                side, party = imports, transfer.payee
            elif transfer.payer in self.export_accounts and sale:
                side, party = exports, transfer.payer
            else:
                continue
            template, reference = self.tables.purpose_code(transfer.purpose)
            side[0].append(party)
            side[1].append(template)
            side[2].append(reference)
            side[3].append(transfer.amount)
        for name, side in (("imports_paid", imports), ("exports_received", exports)):
            if side[0]:
                self.add_pair_amounts(name, self.tables.agent_numbers(side[0]), numpy.array(side[1], dtype=numpy.int64),
                                      _floats(side[3]), numpy.array(side[2], dtype=numpy.int64))

    def note_summed_sales(self, paid: Dict[AgentId, float], income: Dict[AgentId, float],
                          received: Iterable[Tuple[Tuple[AgentId, GoodId], float]],
                          sold: Iterable[Tuple[Tuple[AgentId, GoodId], float]],
                          foreign: Iterable[Tuple[str, Tuple[AgentId, GoodId], float]]) -> None:
        """`note_settlement(..., "sales")` of many goods settlements at once, from their sums: money paid and received by agent,
        goods received and sold by (agent, good), and money across the border ("imports" or "exports") by (agent, good). No
        plant purchase is noted: the buyers are households, which own no plant."""
        tables = self.tables
        if paid:
            self.add_money_out(tables.agent_numbers(list(paid)), _floats(list(paid.values())))
        if income:
            self.add_income(False, tables.agent_numbers(list(income)), _floats(list(income.values())))
        for name, pairs in (("received", list(received)), ("sold", list(sold))):
            if pairs:
                self.add_pair_amounts(name, tables.agent_numbers([key[0] for key, _amount in pairs]),
                                      tables.good_numbers([key[1] for key, _amount in pairs]), _floats([amount for _key, amount in pairs]))
        for side, name in (("imports", "imports_paid"), ("exports", "exports_received")):
            entries = [(key, amount) for each, key, amount in foreign if each == side]
            if entries:
                codes = [tables.purpose_code(SALE_PREFIX + key[1]) for key, _amount in entries]
                self.add_pair_amounts(name, tables.agent_numbers([key[0] for key, _amount in entries]),
                                      numpy.array([code[0] for code in codes], dtype=numpy.int64),
                                      _floats([amount for _key, amount in entries]), numpy.array([code[1] for code in codes], dtype=numpy.int64))

    def note_paid_outside_markets(self, postings: Iterable[Transfer]) -> None:
        """Money paid out in no market (rent, a bonded household's payments, the keep of bonded people): a cost of the payer's
        year, though it takes nothing from the payee's receipts."""
        postings = list(postings)
        if postings:
            self.add_money_out(self.tables.agent_numbers([each.payer for each in postings]), _floats([each.amount for each in postings]))

    def note_wages_outside_markets(self, postings: Iterable[Transfer]) -> None:
        """Pay for work that was not bought in the labour market (a steward's pay): the payer's cost, the payee's wages."""
        postings = list(postings)
        self.note_paid_outside_markets(postings)
        if postings:
            self.add_income(True, self.tables.agent_numbers([each.payee for each in postings]), _floats([each.amount for each in postings]))

    def note_plant_purchases(self, postings: Iterable[object], good: GoodId, plant_goods: Dict[AgentId, Iterable[GoodId]]) -> None:
        """Money producers paid, in the clearing of `good`, for goods their own plant is built from: what they paid the sellers. A seller paid
        nothing but paying to be rid of a negative-priced good is not a buyer, so only receivers of the goods count."""
        postings = list(postings)
        buyers = {posting.receiver for posting in postings if isinstance(posting, GoodsMove)}
        for posting in postings:
            if isinstance(posting, Transfer) and posting.payer in buyers and good in plant_goods.get(posting.payer, ()):
                self.plant_spend.add(posting.payer, posting.amount)
