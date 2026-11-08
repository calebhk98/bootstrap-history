"""The book's numbers of the producers' agents and tiles as arrays in the order of the producer columns, kept on the columns while the
book's numbering and the columns' ids stand (`book.agent_ids` and `book.tile_ids` only grow within a game, so a number never changes;
-1 is a name the book has not numbered)."""
import numpy


def of_columns(columns, book) -> tuple:
    """(agent number of each row of the producer columns, tile number of each tile row of the columns' tiles)."""
    stamp = (id(columns.ids), len(book.agent_ids), len(book.tile_ids), id(book))
    kept = columns.__dict__.get("_book_numbers")
    if kept is None or kept[0] != stamp:
        agents, tiles = book.agent_ids.numbers, book.tile_ids.numbers
        kept = columns.__dict__["_book_numbers"] = (
            stamp, numpy.fromiter((agents.get(name, -1) for name in columns.ids), numpy.int64, len(columns.ids)),
            numpy.fromiter((tiles.get(name, -1) for name in columns.tiles.ids), numpy.int64, len(columns.tiles.ids)))
    return kept[1], kept[2]


_GOODS: dict = {}      # id of a `Names` -> (the names, the book's numbering stamp, the numbers)


def of_goods(goods, book) -> numpy.ndarray:
    """The book's number of each good of `goods` (a `Names`), -1 where it has none, kept while the book's numbering stands."""
    stamp = (len(book.good_ids), id(book))
    kept = _GOODS.get(id(goods))
    if kept is None or kept[0] is not goods or kept[1] != stamp:
        found = book.good_ids.numbers
        if len(_GOODS) > 8:
            _GOODS.clear()
        kept = _GOODS[id(goods)] = (goods, stamp, numpy.fromiter((found.get(name, -1) for name in goods.ids), numpy.int64, len(goods.ids)))
    return kept[2]
