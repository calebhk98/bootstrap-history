"""The labour offers of a year as a table: one row per cohort x trade offer, with the supply parameters as columns.

Replaces the closures `HourSupply` used to carry (a plot schedule per cohort, an hours-sold schedule per market): the hours a
cohort sells at a wage are a function of the columns below, computed by the kernels in `labour_offers_kernels.py`.

Rows are in the order the offers were made (cohort id, then trade, then the seats' and bonded offers after), which fixes every
sum. Ids are numbered per year in sorted order (`LabourIds`); a market is a dense rank of (trade, area) in sorted order."""
from typing import Mapping, NamedTuple, Optional, Sequence, Tuple

import numpy

from sim.compiled_tables.ids import IdTable
from sim.compiled_tables.spec import Column, TableSpec

from .labour_offers_kernels import whole_hours_by_cohort
from .types import AgentId, LabourOffer

LABOUR_OFFERS = TableSpec("LabourOffers", (
    Column("cohort", numpy.int64, "the household cohort that offers the hours", "cohort id", ids="cohorts"),
    Column("trade", numpy.int64, "the trade the hours are offered in", "trade id", ids="trades"),
    Column("area", numpy.int64, "the labour area the hours are offered in", "labour area id", ids="areas"),
    Column("market", numpy.int64, "the labour market (trade, area): rank of the pair in sorted order", "market id"),
    Column("hours", numpy.float64, "hours this offer holds before the cohort keeps any at home", "hours per year"),
    Column("reservation_wage", numpy.float64, "the wage per hour below which the offer is not made; the wage settled at where no wage is known", "money per hour"),
    Column("whole_hours", numpy.float64, "the cohort's hours over all its offers (the year the home share is taken from)", "hours per year"),
    Column("plan_hours", numpy.float64, "hours the cohort keeps for its own-plot plan whatever the wage", "hours per year"),
    Column("work_hours", numpy.float64, "hours the cohort keeps for the household work it does itself", "hours per year"),
    Column("has_plot", numpy.bool_, "whether the cohort keeps hours for a plot at a wage (land held and a need it grows)", "flag"),
    Column("plot_hours_per_worker", numpy.float64, "hours a worker has available to put on the plot", "hours per year per worker"),
    Column("marginal_return", numpy.float64, "what the next plot hour adds with all available hours on it (heuristic input: labour_ask_floor.plot_return_per_hour)", "money per hour"),
    Column("usable_per_worker", numpy.float64, "hours per worker the plot can take: the floors of the needs its land grows", "hours per year per worker"),
    Column("workers", numpy.float64, "working people in the cohort, who multiply the per-worker plot hours", "people"),
    Column("sold_hours", numpy.float64, "output of settle: hours of this offer sold at the wage its market settled at", "hours per year"),
    Column("kept_hours", numpy.float64, "output of settle: hours of this offer not sold (offered hours less sold hours)", "hours per year"),
))
LabourOffers = LABOUR_OFFERS.make_type(__name__)


class PlotParameters(NamedTuple):
    """What the plot keeps at a wage (`households_hours_offered.plot_hours_kept` times `workers`); one per cohort with a plot."""
    per_worker_hours: float
    marginal: float
    usable_per_worker: float
    workers: float


class LabourIds(NamedTuple):
    """The numberings of one year's labour offers, each in sorted name order.

    SEAM: the shared agent numbering (one `IdTable` for producers, cohorts, merchants, the state) plugs in here. When it
    lands, `cohorts` is that table (or a view of its cohort rows) and `labour_ids` only admits trades and areas."""
    cohorts: IdTable
    trades: IdTable
    areas: IdTable

    def market_names(self, market_trades, market_areas) -> Sequence[Tuple[str, str]]:
        return [(self.trades.name(trade), self.areas.name(area)) for trade, area in zip(market_trades.tolist(), market_areas.tolist())]


def labour_ids(offers: Sequence[LabourOffer], extra_cohorts: Sequence[AgentId] = ()) -> LabourIds:
    """Numbers for the cohorts, trades and areas of these offers, each admitted in one sorted batch (`extra_cohorts` are
    cohort names that hold no offer but have plan, work or plot figures)."""
    return LabourIds(IdTable("cohort", {offer.worker for offer in offers}.union(extra_cohorts)),
                     IdTable("trade", {offer.trade for offer in offers}), IdTable("area", {offer.area for offer in offers}))


def market_ranks(trade: numpy.ndarray, area: numpy.ndarray, area_count: int) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """(market of each row, trade of each market, area of each market): markets numbered by (trade, area) in sorted order,
    which is name order because ids are numbered sorted."""
    keys = trade * max(area_count, 1) + area
    unique_keys, market = numpy.unique(keys, return_inverse=True)
    return market.astype(numpy.int64), unique_keys // max(area_count, 1), unique_keys % max(area_count, 1)


class OfferMarkets(NamedTuple):
    """The markets of a table of offers: market m is (trade_of_market[m], area_of_market[m])."""
    trade_of_market: numpy.ndarray
    area_of_market: numpy.ndarray

    def __len__(self) -> int:
        return len(self.trade_of_market)


def _per_cohort(ids: IdTable, values: Mapping[AgentId, float]) -> numpy.ndarray:
    return numpy.array([values.get(name, 0.0) for name in ids.names], dtype=numpy.float64)


def build_labour_offers(offers: Sequence[LabourOffer], plan_hours: Mapping[AgentId, float], work_hours: Mapping[AgentId, float],
                        plot_parameters: Mapping[AgentId, PlotParameters], ids: Optional[LabourIds] = None):
    """(table, ids, markets) for the offers: one row each, in order. The plan, work and plot figures of a cohort are copied
    to each of its rows; `whole_hours` is the sum of the cohort's offered hours added in row order."""
    ids = ids or labour_ids(offers, set(plan_hours) | set(work_hours) | set(plot_parameters))
    cohort = ids.cohorts.admit([offer.worker for offer in offers])
    trade = ids.trades.admit([offer.trade for offer in offers])
    area = ids.areas.admit([offer.area for offer in offers])
    market, market_trade, market_area = market_ranks(trade, area, len(ids.areas))
    names = ids.cohorts.names
    plot = [plot_parameters.get(name) for name in names]
    has_plot = numpy.array([parameters is not None for parameters in plot], dtype=numpy.bool_)
    figure = [numpy.array([getattr(parameters, field) if parameters is not None else 0.0 for parameters in plot]) for field in PlotParameters._fields]
    hours = numpy.array([offer.hours for offer in offers], dtype=numpy.float64)
    count = len(offers)
    table = LABOUR_OFFERS.table_of(
        LabourOffers, cohort=cohort, trade=trade, area=area, market=market, hours=hours,
        reservation_wage=numpy.array([offer.reservation_wage for offer in offers], dtype=numpy.float64),
        whole_hours=numpy.zeros(count), plan_hours=_per_cohort(ids.cohorts, plan_hours)[cohort],
        work_hours=_per_cohort(ids.cohorts, work_hours)[cohort], has_plot=has_plot[cohort],
        plot_hours_per_worker=figure[0][cohort], marginal_return=figure[1][cohort], usable_per_worker=figure[2][cohort],
        workers=figure[3][cohort], sold_hours=numpy.zeros(count), kept_hours=numpy.zeros(count))
    table.whole_hours[:] = whole_hours_by_cohort(table, len(names))[cohort]
    return table, ids, OfferMarkets(market_trade, market_area)
