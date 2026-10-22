"""The hours households sell, as a schedule against the wage (Complaints 473, 608).

A household's year of hours goes first to its own-plot plan and the household work it does itself (both fixed for the
year), then to its plot as far as an hour there beats the wage (`households_hours_offered.plot_hours_kept`), and of
what is left a share to leisure by the preference of its trade (`leisure_hours_kept`); the rest it sells. Every use but
the plan and the work depends on the wage, so the hours sold rise smoothly with it. The labour core clears each market
against this schedule (`hours_share_at`), then the hours each offer sold, and the hours kept for each use, are read
at the wage the market cleared at. Plain functions of built inputs.
"""
import dataclasses
from typing import Callable, Dict, List, Mapping, Sequence, Tuple

from . import households_hours_offered
from .types import AgentId, LabourOffer


@dataclasses.dataclass
class HourSupply:
    offers: Sequence[LabourOffer]                       # every offer, with the cohort's whole year of hours
    plan_hours: Mapping[AgentId, float]                 # own-plot plan hours a cohort keeps whatever the wage
    work_hours: Mapping[AgentId, float]                 # household work it does itself
    plot_hours_at: Mapping[AgentId, Callable[[float], float]]   # hours its plot keeps at a wage (households_hours_offered.plot_hours_kept)
    plot_usable: Mapping[AgentId, float]                # hours its plot could use in all, whatever the wage
    anchor_wage: Mapping[str, float]                    # trade -> leisure anchor wage, in this year's prices
    faced_wage: Mapping[Tuple[str, str], float] = dataclasses.field(default_factory=dict)   # (trade, area) -> wage where no market cleared
    # filled by `settle`
    sold: List[LabourOffer] = dataclasses.field(default_factory=list)
    kept: Dict[AgentId, float] = dataclasses.field(default_factory=dict)
    leisure: Dict[AgentId, float] = dataclasses.field(default_factory=dict)

    def __post_init__(self) -> None:
        self._hours: Dict[AgentId, float] = {}
        for offer in self.offers:
            self._hours[offer.worker] = self._hours.get(offer.worker, 0.0) + offer.hours

    def parts(self, offer: LabourOffer, wage: float) -> Tuple[float, float, float]:
        """(hours kept for plot and household work, hours free after them, hours of those free that may be leisure) of
        one offer at this wage: hours the plot could still use to grow the floors are not leisure."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return 0.0, 0.0, 0.0
        plot = self.plot_hours_at.get(offer.worker)
        plot_kept = max(self.plan_hours.get(offer.worker, 0.0), plot(wage) if plot else 0.0)
        fixed = plot_kept + self.work_hours.get(offer.worker, 0.0)
        share = offer.hours / whole
        free = offer.hours - min(fixed, whole) * share
        still_usable = max(0.0, self.plot_usable.get(offer.worker, 0.0) - plot_kept) * share
        return min(fixed, whole) * share, free, max(0.0, free - still_usable)

    def split(self, offer: LabourOffer, wage: float) -> Tuple[float, float, float]:
        """(hours sold, hours kept for plot and household work, hours at leisure) of one offer at this wage."""
        at_home, free, eligible = self.parts(offer, wage)
        rest = households_hours_offered.leisure_hours_kept(eligible, wage, self.anchor_wage.get(offer.trade))
        return free - rest, at_home, rest

    def sold_hours_schedule(self, offer: LabourOffer) -> Callable[[float], float]:
        """The hours of one offer sold at a wage, as `split(offer, wage)[0]` gives them, with what does not depend on
        the wage worked out once: for a schedule asked at many wages."""
        whole = self._hours.get(offer.worker, 0.0)
        if whole <= 0.0 or offer.hours <= 0.0:
            return lambda wage: 0.0
        plot = self.plot_hours_at.get(offer.worker)
        plan = self.plan_hours.get(offer.worker, 0.0)
        work = self.work_hours.get(offer.worker, 0.0)
        usable = self.plot_usable.get(offer.worker, 0.0)
        anchor = self.anchor_wage.get(offer.trade)
        share = offer.hours / whole
        hours = offer.hours
        elasticity = households_hours_offered.LEISURE_ELASTICITY
        leisure_valued = anchor is not None and anchor > 0.0      # `leisure_share`, with its tests done once

        def sold(wage: float) -> float:
            plot_kept = max(plan, plot(wage) if plot else 0.0)
            free = hours - min(plot_kept + work, whole) * share
            if not leisure_valued:
                return free
            eligible = max(0.0, free - max(0.0, usable - plot_kept) * share)
            if wage <= 0.0:
                return free - eligible * 1.0
            return free - eligible * (1.0 / (1.0 + (wage / anchor) ** elasticity))
        return sold

    def share_at(self, trade: str, area: str) -> Callable[[float], float]:
        """The share of a market's hours sold at a wage, over the offers in it."""
        return self._share_over([offer for offer in self.offers if offer.trade == trade and offer.area == area])

    def _share_over(self, in_market: Sequence[LabourOffer]) -> Callable[[float], float]:
        mine = [offer for offer in in_market if offer.hours > 0.0]
        total = sum(offer.hours for offer in mine)
        schedules = [self.sold_hours_schedule(offer) for offer in mine]

        def share(wage: float) -> float:
            return sum([schedule(wage) for schedule in schedules]) / total if total > 0.0 else 0.0
        return share

    def shares(self) -> Dict[Tuple[str, str], Callable[[float], float]]:
        by_market: Dict[Tuple[str, str], List[LabourOffer]] = {}
        for offer in self.offers:
            by_market.setdefault((offer.trade, offer.area), []).append(offer)      # in offer order, as share_at reads them
        return {market: self._share_over(by_market[market]) for market in sorted(by_market)}

    def settle(self, wage_by_market: Mapping[Tuple[str, str], float]) -> List[LabourOffer]:
        """The offers as sold at the wages the markets cleared at (the faced wage where one did not), and the hours
        each cohort kept in all and as leisure."""
        self.sold, self.kept, self.leisure = [], {}, {}
        for offer in self.offers:
            market = (offer.trade, offer.area)
            wage = wage_by_market.get(market, self.faced_wage.get(market, offer.reservation_wage))
            sold, at_home, rest = self.split(offer, wage)
            self.sold.append(dataclasses.replace(offer, hours=sold))
            self.kept[offer.worker] = self.kept.get(offer.worker, 0.0) + (offer.hours - sold)
            if rest > 0.0:
                self.leisure[offer.worker] = self.leisure.get(offer.worker, 0.0) + rest
        return self.sold
