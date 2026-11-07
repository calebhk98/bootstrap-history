"""Complaint 497: `hire_through_rounds` gives the answers of the plain loop it replaced, on random inputs; no game."""

QUICK_TOPIC = True

import random
import unittest

from sim.labour.market import applications
from sim.labour.market.applications import SEARCH_ROUNDS_PER_YEAR, SEPARATION_SHARE_PER_ROUND, Searchers


def plain_hire_through_rounds(hired, kept, wanted, offers, pool, ask, floor, ceilings=None):
    """The round loop as it was written before the per-count lines were shared."""
    groups = [Searchers(pool, ask)]
    taken, paid_sum = {}, {}
    for _ in range(SEARCH_ROUNDS_PER_YEAR):
        for employer in sorted(hired):
            held = hired[employer]
            if held <= 0.0:
                continue
            groups.append(Searchers(held * SEPARATION_SHARE_PER_ROUND, offers.get(employer, 0.0)))
            hired[employer] = held * (1.0 - SEPARATION_SHARE_PER_ROUND)
            kept[employer] *= 1.0 - SEPARATION_SHARE_PER_ROUND
        vacancies = {employer: max(0.0, wanted[employer] - hired[employer]) for employer in wanted}
        groups = applications.capped_asks(groups, vacancies, offers)
        reach, units = applications._round(groups, vacancies, offers)
        for group, count in zip(groups, reach):
            unit = units[count]
            for employer, share in unit.items():
                hired[employer] += group.hours * share
                taken[employer] = taken.get(employer, 0.0) + group.hours * share
                paid_sum[employer] = paid_sum.get(employer, 0.0) + group.hours * share * offers[employer]
            group.hours -= group.hours * sum(unit.values())
        groups = [Searchers(group.hours, applications.lowered_ask(group.ask, floor)) for group in groups if group.hours > 1e-9]
        if ceilings is not None:
            for employer in wanted:
                offers[employer] = applications.raised_offer(offers.get(employer, 0.0), ceilings.get(employer, 0.0),
                                                             wanted[employer], hired[employer])
    for employer, hours in taken.items():
        if hours > 0.0:
            offers[employer] = paid_sum[employer] / hours
    return taken


class HiringThroughRoundsKeepsItsValues(unittest.TestCase):

    def test_matches_the_plain_loop_exactly(self):
        rng = random.Random(11)
        for _case in range(80):
            names = ["e%02d" % i for i in range(rng.randint(1, 14))]
            wanted = {name: rng.uniform(0.0, 4000.0) for name in names}
            hired = {name: rng.choice([0.0, rng.uniform(0.0, 3000.0)]) for name in names}
            offers = {name: rng.choice([1.0, 1.5, rng.uniform(0.5, 3.0)]) for name in names}
            ceilings = rng.choice([None, {name: rng.uniform(1.0, 4.0) for name in names}])
            arguments = (rng.uniform(0.0, 9000.0), rng.uniform(0.5, 3.5), rng.uniform(0.1, 1.0))
            kept = {name: rng.uniform(0.0, 3000.0) for name in names}
            fast = (dict(hired), dict(kept), dict(offers))
            plain = (dict(hired), dict(kept), dict(offers))
            got = applications.hire_through_rounds(fast[0], fast[1], wanted, fast[2], *arguments, ceilings)
            expected = plain_hire_through_rounds(plain[0], plain[1], wanted, plain[2], *arguments, ceilings)
            self.assertEqual(list(got.items()), list(expected.items()))
            self.assertEqual(fast, plain)


if __name__ == "__main__":
    unittest.main()
