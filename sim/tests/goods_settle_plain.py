"""`goods_settle.settle_good` for a good whose markets all traded in the batch as it was before `goods_settle_one_call`: `settle_by_ids`, then
the ledger's notes by several calls, kept so the one-call kernel is tested against it."""
from typing import Dict

import numpy

from sim.economy.goods_settle import GoodSettlement, _note_mint_takes
from sim.economy.settlement_ids import settle_by_ids
from sim.economy.settlement_note_kernel import FOREIGN_MARKET, note_columns
from sim.economy.year_ledger_tables import SALES_PURPOSE


def plain_settle_good(record, ledger, cleared, good: str, plant_makers: Dict[str, list]) -> GoodSettlement:
    """The by-ids branch of `settle_good` (every market that traded is a `TableClearing` of the batch)."""
    book = record.book
    slots = numpy.flatnonzero(cleared.quantity > 0.0).tolist()
    answer = GoodSettlement(len(cleared))
    if not slots:
        return answer
    settled = settle_by_ids(book, cleared.batch, cleared.slots[slots], cleared.context.setup.currency_id, good, "sale of %s" % good,
                            ledger.import_accounts, ledger.export_accounts)
    if settled is None:
        return answer
    tables = ledger.tables
    tables.fit_agents()
    makers = numpy.sort(numpy.array([book.agent_ids.numbers[name] for name in plant_makers.get(good, ()) if name in book.agent_ids.numbers],
                                    dtype=numpy.int64))
    (purpose_kind, good_column, template, reference, plant_bought, any_foreign, *bought) = note_columns(
        settled.agent_offset, numpy.array(slots, dtype=numpy.int64), settled.agent, settled.paid, settled.got_goods, settled.paid_as_buyer,
        settled.buyer_net, settled.goods_in, settled.imports, settled.exports, makers, SALES_PURPOSE, book.good_number(good))
    if any_foreign:
        slot = template == FOREIGN_MARKET
        template[slot], reference[slot] = tables.purpose_code("sale of %s" % good)
    ledger.note_settlement_rows(settled.agent, settled.paid, settled.received, settled.imports, settled.exports, settled.got_goods,
                                settled.goods_in, settled.goods_out, purpose_kind, good_column, template, reference, plant_bought)
    cleared.bought = tuple(bought)
    answer.delivered[slots] = settled.delivered
    answer._by_ids = (book.agent_ids.name_list, settled, {position: place for place, position in enumerate(slots)})
    _note_mint_takes(book, settled, slots, answer)
    return answer
