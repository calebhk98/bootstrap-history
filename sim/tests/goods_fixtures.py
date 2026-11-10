"""A goods record for a test's fixture: the stores the economy keeps by market, as columns of the memory's numbering."""
from sim.economy.goods_record import GoodsRecord


def goods_on(memory) -> GoodsRecord:
    """An empty `GoodsRecord` whose per-market columns are indexed by `memory`'s goods-market numbering."""
    goods = GoodsRecord()
    goods.bind_markets(memory.tables)
    return goods
