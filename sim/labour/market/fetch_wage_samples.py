"""Sample calls of the `fetch_wage` kernel, built in code from fixed tables: they stand in for stored inputs, and the quick-tier
rule test and a mod's equivalence check run the same ones. Each case names the branch it takes."""
import random
from typing import Callable, Dict, List, Sequence, Tuple

Case = Dict[str, object]

CASES: Dict[str, Case] = {
    # the workers on the spot already sell the hours wanted at the going wage
    "enough_at_home": dict(area="a", wanted=100.0, going=1.0, top=3.0, offers=[(1.5, "b")],
                           everyone={"a": 400.0, "b": 300.0}, bids={}, shares={"a": [(0.0, 1.0)]}),
    # the nearest source fills the shortage at the wage it comes at
    "first_source_fills": dict(area="a", wanted=500.0, going=1.0, top=4.0, offers=[(1.5, "b"), (2.5, "c")],
                               everyone={"a": 300.0, "b": 400.0, "c": 400.0}, bids={"b": 100.0}, shares={}),
    # hours rise with the wage, so the filling wage lies between two ways in and is found by bisection
    "bisected_between_sources": dict(area="a", wanted=400.0, going=1.0, top=5.0, offers=[(1.5, "b"), (4.0, "c")],
                                     everyone={"a": 300.0, "b": 400.0, "c": 300.0}, bids={"b": 50.0},
                                     shares={"a": [(0.0, 0.4), (4.0, 0.8)], "b": [(0.0, 0.5), (4.0, 1.0)]}),
    # every source together falls short at its wage; a higher wage draws the hours the workers keep back
    "filled_only_at_the_top": dict(area="a", wanted=590.0, going=1.0, top=6.0, offers=[(1.5, "b")],
                                   everyone={"a": 400.0, "b": 300.0}, bids={"b": 100.0},
                                   shares={"a": [(0.0, 0.3), (6.0, 1.0)], "b": [(0.0, 0.5), (6.0, 1.0)]}),
    # nothing fills it
    "never_filled": dict(area="a", wanted=5000.0, going=1.0, top=6.0, offers=[(1.5, "b"), (2.0, "c")],
                         everyone={"a": 100.0, "b": 100.0, "c": 100.0}, bids={}, shares={}),
    # no area to fetch from
    "no_way_in": dict(area="a", wanted=300.0, going=1.0, top=2.0, offers=[], everyone={"a": 100.0},
                      bids={}, shares={"a": [(0.0, 0.5), (2.0, 1.0)]}),
}


def _random_case(seed: int) -> Case:
    rng = random.Random(seed)
    areas = ["a%d" % index for index in range(6)]
    return dict(area="a0", wanted=rng.uniform(200.0, 2500.0), going=rng.uniform(0.5, 1.5), top=rng.uniform(3.0, 7.0),
                offers=[(rng.uniform(1.0, 5.0), other) for other in areas[1:] if rng.random() < 0.85],
                everyone={area: rng.uniform(50.0, 700.0) for area in areas},
                bids={area: rng.uniform(0.0, 300.0) for area in areas if rng.random() < 0.5},
                shares={area: [(0.0, rng.uniform(0.2, 0.7)), (7.0, rng.uniform(0.8, 1.0))] for area in areas if rng.random() < 0.7})


def _schedule(points: Sequence[Tuple[float, float]]) -> Callable[[float], float]:
    """The share of an area's hours sold at a wage: straight lines between the points, flat beyond them."""
    def share(wage: float) -> float:
        if wage <= points[0][0]:
            return points[0][1]
        for (low_wage, low_share), (high_wage, high_share) in zip(points, points[1:]):
            if wage <= high_wage:
                return low_share + (high_share - low_share) * (wage - low_wage) / (high_wage - low_wage)
        return points[-1][1]
    return share


def call_of(case: Case):
    """((arguments), {}) of one `fetch_wage` call: the lookups answer from the case's tables as `ImportCosts` answers from its own."""
    everyone, bids, shares = case["everyone"], case["bids"], {area: _schedule(points) for area, points in case["shares"].items()}

    def hours_at(area: str, wage: float) -> float:
        whole = everyone.get(area, 0.0)
        return whole if area not in shares else whole * shares[area](wage)

    def wanted_at(area: str) -> float:
        return bids.get(area, 0.0)

    def spare_of(sources: Sequence[str]) -> Tuple[List[float], float]:
        remaining = [max(0.0, everyone.get(other, 0.0) - bids.get(other, 0.0)) for other in sources]
        return remaining, sum(remaining)
    return (case["area"], case["wanted"], case["going"], case["top"], lambda: list(case["offers"]), hours_at, wanted_at, spare_of), {}


def samples() -> List[Tuple[tuple, dict]]:
    return [call_of(case) for case in CASES.values()] + [call_of(_random_case(seed)) for seed in range(8)]
