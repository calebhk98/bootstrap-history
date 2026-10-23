"""Complaint 382: wages and the state's pay reach the people's purses and no money is made or lost on the way. Rule:
`payroll.pay_wages` shares the amount among the home country's free strata by members, or pays the workers edge while
there are none; `ActorsMixin.pay_wages` is the founder's household paying through it."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import payroll
from sim.agents.edges import EDGE_WORKERS
from sim.engine.society_actors import ActorsMixin


class Purse:
    def __init__(self, money=0.0, members=0.0, country=None, exited_year=None, bonded=False):
        self.money = money
        self.record = SimpleNamespace(members=members, country=country, exited_year=exited_year)
        self.bonded = bonded
        self.income = []

    def is_bonded(self):
        return self.bonded

    def debit(self, amount, purpose):
        self.money -= amount

    def credit(self, amount, purpose):
        self.money += amount
        self.income.append(purpose)


class Registry:
    def __init__(self, strata):
        self.strata = strata

    def of_kind(self, kind):
        return self.strata if kind == "stratum" else []


class World:
    def __init__(self):
        self.workers_edge = Purse()

    def edge(self, name):
        assert name == EDGE_WORKERS
        return self.workers_edge


class PayWagesTests(unittest.TestCase):
    def test_wages_are_shared_among_free_strata_by_members(self):
        payer, small, large = Purse(1000.0), Purse(members=100.0), Purse(members=300.0)
        payroll.pay_wages(Registry([small, large]), payer, 400.0, "living costs", World())
        self.assertAlmostEqual(small.money, 100.0)
        self.assertAlmostEqual(large.money, 300.0)

    def test_what_the_payer_loses_the_people_gain(self):
        payer, first, second, third = Purse(1000.0), Purse(members=7.0), Purse(members=11.0), Purse(members=13.0)
        payroll.pay_wages(Registry([first, second, third]), payer, 333.33, "living costs", World())
        self.assertAlmostEqual(1000.0 - payer.money, first.money + second.money + third.money, places=9)
        self.assertAlmostEqual(first.money + second.money + third.money, 333.33, places=9)

    def test_the_payment_is_labelled_with_its_purpose(self):
        payer, people = Purse(100.0), Purse(members=1.0)
        payroll.pay_wages(Registry([people]), payer, 10.0, "living costs", World())
        self.assertEqual(people.income, ["living costs"])

    def test_bonded_foreign_departed_and_empty_strata_are_not_paid(self):
        payer, free = Purse(1000.0), Purse(members=10.0)
        others = [Purse(members=10.0, bonded=True), Purse(members=10.0, country="abroad"),
                  Purse(members=10.0, exited_year=-50), Purse(members=0.0)]
        payroll.pay_wages(Registry([free] + others), payer, 100.0, "living costs", World())
        self.assertAlmostEqual(free.money, 100.0)
        self.assertEqual([purse.money for purse in others], [0.0] * 4)

    def test_with_no_strata_the_wages_go_to_the_workers_edge(self):
        payer, world = Purse(1000.0), World()
        payroll.pay_wages(Registry([]), payer, 250.0, "living costs", world)
        self.assertEqual(world.workers_edge.money, 250.0)
        self.assertEqual(payer.money, 750.0)

    def test_the_founders_household_pays_its_wages_through_the_same_rule(self):
        household, people = Purse(1000.0), Purse(members=5.0)
        founder_world = SimpleNamespace(actors=Registry([people]), state=SimpleNamespace(household=household),
                                        edge=lambda name: Purse())
        ActorsMixin.pay_wages(founder_world, 120.0, "living costs")
        self.assertEqual((household.money, people.money), (880.0, 120.0))


if __name__ == "__main__":
    unittest.main()
