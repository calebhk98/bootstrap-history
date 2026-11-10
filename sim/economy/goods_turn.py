"""The producers' turn in a good's clearing, over the year arrays: who works this turn, what they make, and what they offer, each a
call or two over whole columns and no per-producer Python.

`TurnWorld` is built once per year from the year arrays (`goods_turn_spec` for the recipes, the book's numbers of the producers, goods,
tiles and trades as arrays). `produce` is `goods_production.produce` and `offer` is the quick part of `year_goods._produce_and_offer`
(`year_goods_offers.offer_reservations` for the prices), writing the offers as rows of the order tables; the producers that
`goods_turn_offers_kernel` calls slow are returned for `producers.offers` to make one at a time, in their place in the order."""
from typing import Dict, List, Optional, Sequence

import numpy

from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK

from . import goods_turn_spec, year_goods_offers
from .goods_order_tables import PRODUCER_OUTPUT
from .goods_turn_kernel import produce_turn
from .goods_turn_offer_kernel import offer_turn
from .inventory import DISTRESS_CURVE_EXPONENT
from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR
from .types import EDGE_CONSUMPTION, EDGE_PRODUCTION, GoodsMove
from .year_arrays_memory import markets_by_good_tile


class Numbered:
    """The numbers an id table gives a fixed list of names, as an array (-1: not numbered), read again when the table has numbered more."""

    def __init__(self, names: Sequence[str], table_of):
        self.names, self._table_of = list(names), table_of
        self._seen = None
        self._numbers = None

    def array(self) -> numpy.ndarray:
        table = self._table_of()
        stamp = (id(table), len(table))
        if self._seen != stamp:
            found = table.numbers
            self._numbers = numpy.array([found.get(name, -1) for name in self.names], dtype=numpy.int64)
            self._seen = stamp
        return self._numbers


def _runs_column(plans, producers) -> numpy.ndarray:
    """The runs planned for each producer of the columns (NaN: no plan); the plan table's column when it covers the same producers."""
    ids = getattr(plans, "ids", None)
    if ids is not None and tuple(ids) == producers.ids:
        return numpy.array(plans.runs, dtype=float)
    return numpy.array([numpy.nan if (plan := plans.get(each)) is None else plan.runs for each in producers.ids], dtype=float)


class TurnWorld:
    """The year's producers' turns over the arrays."""

    def __init__(self, setup, record, view, ledger, arrays, costs, spec, plans):
        self.setup, self.record, self.view, self.ledger, self.arrays, self.costs, self.spec = setup, record, view, ledger, arrays, costs, spec
        book = record.book
        matrices, producers = arrays.matrices, arrays.producers
        self.agents = Numbered(producers.ids, lambda: book.agent_ids)
        self.goods = Numbered(matrices.goods.ids, lambda: book.good_ids)
        self.tiles = Numbered(arrays.tiles.ids, lambda: book.tile_ids)
        self.trades = Numbered(matrices.trades.ids, lambda: ledger.tables.markets.trades)
        self.runs = _runs_column(plans, producers)
        self.done = numpy.zeros(len(producers.ids), dtype=bool)
        self.markets = markets_by_good_tile(record.memory, matrices.goods, arrays.area_index)
        self._makers: Dict[int, numpy.ndarray] = {}        # a good's column -> the positions of the producers whose recipe makes it

    @classmethod
    def of(cls, setup, record, view, ledger, arrays, costs, plans) -> Optional["TurnWorld"]:
        """The world of the year's turns, or None where the old per-producer path must run (a recipe naming something the arrays lack,
        a storage cost, which needs the area's money)."""
        spec = goods_turn_spec.of(setup, arrays.matrices)
        if spec is None or not year_goods_offers.usable():
            return None
        return cls(setup, record, view, ledger, arrays, costs, spec, plans)

    def take_turn(self, good: str) -> numpy.ndarray:
        """The positions (in the producer columns, in id order) of the producers that make `good` and have not had their turn;
        they have it now."""
        column = self.arrays.matrices.goods.row.get(good)
        if column is None:
            return numpy.empty(0, dtype=numpy.int64)
        makers = self._makers.get(column)
        if makers is None:
            makers = self._makers[column] = numpy.flatnonzero(self.spec.has_output[self.arrays.producers.recipe_row, column])
        found = makers[~self.done[makers]]
        self.done[found] = True
        return found

    def ids_of(self, positions) -> List[str]:
        return [self.arrays.producers.ids[position] for position in positions.tolist()]

    # ---- making -------------------------------------------------------------------------------

    def produce(self, positions: numpy.ndarray) -> numpy.ndarray:
        """The producers at `positions` make what their plans, stocks and hired hours allow, booked together and noted in the ledger's
        output. Returns the positions of those with runs planned."""
        planned = positions[self.runs[positions] > 0.0]
        if not len(planned):
            return planned
        columns = self.arrays.producers
        spec, book, tables = self.spec, self.record.book, self.ledger.tables
        tables.flush()
        stock = book.stock_rows
        hours = tables.pairs["hours_hired"].rows
        agent, tile = self.agents.array()[positions], self.tiles.array()[columns.tile_row[positions]]
        made = produce_turn(
            self.runs[positions], agent, tile, columns.recipe_row[positions], columns.capacity_runs[positions],
            columns.yield_factor[positions], positions, columns.hours_scale, spec.hard_ptr, spec.hard_good, spec.hard_per_run,
            spec.wear_ptr, spec.wear_draw, spec.wear_per_run, spec.step_ptr, spec.step_draw, spec.step_units, spec.step_factor,
            spec.step_trade_ptr, spec.step_trade_slot, spec.draw_ptr, spec.draw_good, spec.draw_listed, spec.labour_ptr,
            spec.labour_trade, spec.labour_hours, spec.output_ptr, spec.output_good, spec.output_per_run, spec.lines_most,
            self.goods.array(), self.trades.array(), stock.table.key, stock.table.quantity, stock.index, hours.table.key,
            hours.table.amount, hours.index)
        self._post(positions, *made)
        return planned

    def _post(self, positions, place, good_row, quantity, is_output) -> None:
        """Note the outputs in the ledger and book every move as one batch of posting rows (all or none); a name the book has not numbered, or a
        refusal, goes through `Book.move_many`, which numbers it or raises its own error."""
        if not len(place):
            return
        book, producers = self.record.book, self.arrays.producers
        owner = positions[place]
        agent = self.agents.array()[owner]
        tile = self.tiles.array()[producers.tile_row[owner]]
        good = self.goods.array()[good_row]
        edge_in, edge_out = book.agent_ids.numbers.get(EDGE_CONSUMPTION, -1), book.agent_ids.numbers.get(EDGE_PRODUCTION, -1)
        giver = numpy.where(is_output, edge_out, agent)
        receiver = numpy.where(is_output, agent, edge_in)
        self._note_output(agent, good, quantity, is_output, owner, good_row)
        if (giver < 0).any() or (receiver < 0).any() or (good < 0).any() or (tile < 0).any():
            book.move_many(self._moves(owner, good_row, quantity, is_output))
            return
        in_code, out_code = book.purposes.encode("input"), book.purposes.encode("output")
        count = len(place)
        moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, count, giver, receiver, good, tile, tile, quantity,
                           numpy.where(is_output, out_code[0], in_code[0]), numpy.where(is_output, out_code[1], in_code[1]),
                           numpy.zeros(count, dtype=numpy.int64))
        outcomes, _scratch = book.apply_postings(table_from(TRANSFER_POSTINGS, TransferPostings, 0,
                                                            *[[] for _column in TRANSFER_POSTINGS.columns]), moves, 1)
        if int(outcomes.code[0]) != OK:
            book.move_many(self._moves(owner, good_row, quantity, is_output))        # the book's own refusal

    def _note_output(self, agent, good, quantity, is_output, owner, good_row) -> None:
        """The goods made, added to the ledger's output of the producer that receives them."""
        if not is_output.any():
            return
        tables = self.ledger.tables
        if (agent[is_output] < 0).any() or (good[is_output] < 0).any():
            names_agent = [self.arrays.producers.ids[each] for each in owner[is_output].tolist()]
            names_good = [self.arrays.matrices.goods.ids[each] for each in good_row[is_output].tolist()]
            agents_made, goods_made = tables.agent_numbers(names_agent), tables.good_numbers(names_good)
        else:
            tables.fit_agents()
            agents_made, goods_made = agent[is_output], good[is_output]
        self.ledger.add_pair_amounts("output", agents_made, goods_made, quantity[is_output])

    def _moves(self, owner, good_row, quantity, is_output) -> List[GoodsMove]:
        """The moves by name (the edge agents stand for what is consumed and what is made)."""
        producers, matrices = self.arrays.producers, self.arrays.matrices
        moves = []
        for each, row, units, made in zip(owner.tolist(), good_row.tolist(), quantity.tolist(), is_output.tolist()):
            name, tile = producers.ids[each], self.arrays.tiles.ids[producers.tile_row[each]]
            moves.append(GoodsMove(EDGE_PRODUCTION, name, matrices.goods.ids[row], tile, units, "output") if made else
                         GoodsMove(name, EDGE_CONSUMPTION, matrices.goods.ids[row], tile, units, "input"))
        return moves

    # ---- offering -----------------------------------------------------------------------------

    def offer(self, positions: numpy.ndarray, rate: float, orders, slow_offers) -> None:
        """The offers of the producers at `positions` (in id order) written to the order tables as rows, in the producers' order. A producer
        with an output held but no price expected is passed, with the cash it presses to raise, to `slow_offers(position, shortfall)`,
        which adds its offers itself, at its place in the order."""
        if not len(positions):
            return
        columns, spec, book = self.arrays.producers, self.spec, self.record.book
        stock = book.stock_rows
        agents = self.agents.array()[positions]
        cash = book.balances_at(agents, self.setup.currency_id)
        slow, shortfall, quick_place, pair_good, pair_units, reservation = offer_turn(
            positions, self.agents.array(), self.tiles.array(), columns.tile_row, columns.recipe_row, columns.capacity_runs,
            spec.output_ptr, spec.output_good, spec.output_kept, spec.spoilage, self.goods.array(), self.costs.expected,
            self.costs.slot_of, stock.table.key, stock.table.quantity, stock.index, cash, self.ledger.running_costs_at(agents),
            columns.cash_target, columns.last_runs, columns.expected_sales, self.costs.pays, float(rate),
            OUTPUT_CHANGE_SHARE_PER_YEAR, DISTRESS_CURVE_EXPONENT)
        pairs = (pair_good, pair_units, reservation)
        written = 0
        for each in numpy.flatnonzero(slow).tolist() + [len(positions)]:
            upto = int(numpy.searchsorted(quick_place, each, side="left"))
            self._write(orders, positions[quick_place[written:upto]], *[part[written:upto] for part in pairs])
            written = upto
            if each < len(positions):
                slow_offers(int(positions[each]), float(shortfall[each]))

    def _write(self, orders, owners, good_rows, units, reservation) -> None:
        """Offer rows of the pairs: the sellers, goods and tiles numbered (a name the book has not met is numbered now, in name order),
        the markets from the grid (one the memory has not numbered is numbered through `orders.market_ids`)."""
        if not len(owners):
            return
        columns, matrices = self.arrays.producers, self.arrays.matrices
        tile_rows = columns.tile_row[owners]
        sellers, goods, tiles = self.agents.array()[owners], self.goods.array()[good_rows], self.tiles.array()[tile_rows]
        if (sellers < 0).any():
            sellers = numpy.array(orders.agent_ids_of([columns.ids[each] for each in owners.tolist()]), dtype=numpy.int64)
        if (goods < 0).any():
            goods = numpy.array(orders.good_ids_of([matrices.goods.ids[each] for each in good_rows.tolist()]), dtype=numpy.int64)
        if (tiles < 0).any():
            tiles = numpy.array(orders.tile_ids_of([self.arrays.tiles.ids[each] for each in tile_rows.tolist()]), dtype=numpy.int64)
        market = self.markets[good_rows, tile_rows]
        missing = numpy.flatnonzero(market < 0).tolist()
        if missing:
            market = market.copy()
            names = [matrices.goods.ids[good_rows[each]] for each in missing]
            market[missing] = orders.market_ids(names, [self.view.area_of(name, self.arrays.tiles.ids[tile_rows[each]])
                                                        for name, each in zip(names, missing)])
        orders.append_offers(sellers, goods, tiles, market, units, reservation, PRODUCER_OUTPUT)
