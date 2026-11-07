"""Numba port, labour switching: `switching_kernel.group_moves` groups a round's moves by (destination, share of the training
years) exactly as the numpy grouping it replaced (np.unique on a key, groups in order of first appearance); no game."""

QUICK_TOPIC = True

import random
import unittest

import numpy as np

from sim.labour.market import switching_kernel


def grouped_with_numpy(destinations, shares):
    share_rank = np.unique(shares, return_inverse=True)[1].reshape(-1)
    key = destinations * (int(share_rank.max()) + 1) + share_rank
    _keys, first, group_of = np.unique(key, return_index=True, return_inverse=True)
    group_of = group_of.reshape(-1)
    count = first.shape[0]
    rank_of_group = np.empty(count, np.int64)
    rank_of_group[np.argsort(first, kind="stable")] = np.arange(count)
    members = np.argsort(rank_of_group[group_of], kind="stable")
    starts = np.zeros(count + 1, np.int64)
    np.cumsum(np.bincount(rank_of_group[group_of], minlength=count), out=starts[1:])
    return count, rank_of_group[group_of], members, starts


class GroupMovesAgreeWithNumpyGrouping(unittest.TestCase):

    def test_random_moves(self):
        rng = random.Random(7)
        for _case in range(300):
            count = rng.randint(1, 40)
            destinations = np.array([rng.randint(0, 5) for _ in range(count)], np.int64)
            shares = np.array([rng.choice([0.3, 1.0, 0.5]) for _ in range(count)])
            group_of, members, starts = np.empty(count, np.int64), np.empty(count, np.int64), np.zeros(count + 1, np.int64)
            groups = switching_kernel.group_moves(destinations, shares, group_of, members, starts)
            expected_groups, expected_of, expected_members, expected_starts = grouped_with_numpy(destinations, shares)
            self.assertEqual(groups, expected_groups)
            self.assertEqual(group_of.tolist(), expected_of.tolist())
            self.assertEqual(members.tolist(), expected_members.tolist())
            self.assertEqual(starts[:groups + 1].tolist(), expected_starts.tolist())


if __name__ == "__main__":
    unittest.main()
