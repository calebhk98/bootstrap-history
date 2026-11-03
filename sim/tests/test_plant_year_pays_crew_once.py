"""Complaint 514: a plant's year pays the crew once. `business_books.operate` charges the non-crew upkeep to suppliers once
and pays no wages itself (the labour core's clearing pays the crew), takings scale with the crew found, and the margin it
returns is takings less upkeep and the crew's wage bill. The stand-ins carry only what `operate` reads; staffing is a recorder."""
QUICK_TOPIC = True

from sim.tests.agents_fake_world import flat_world
import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents import business_books


class Purse:
    def __init__(self, name):
        self.name = name
        self.balance = 0.0
        self.record = SimpleNamespace(country=None)
        self.income, self.outlays = [], []

    payments = property(lambda self: self)   # a stand-in party pays through itself

    def debit(self, amount, purpose):
        self.balance -= amount
        self.outlays.append((purpose, amount))

    def credit(self, amount, purpose):
        self.balance += amount
        self.income.append((purpose, amount))


class Business:
    def size_of(self, key):
        return 1.0

    def opened_year_of(self, key, year):
        return 0

    def note_crew_found(self, key, found):
        self.crew_found = found

    def note_takings(self, key, takings):
        self.takings = takings


@flat_world
class World:
    year = 10

    def __init__(self, books):
        self.books = books
        self.edges = {}

    def plant_books(self, key, opened, rivals, size):
        return self.books

    def edge(self, name):
        return self.edges.setdefault(name, Purse(name))

    def sells_on_book(self, key):
        return False

    def government(self):
        return SimpleNamespace(collect=lambda owner, takings, world: 0.0)

    def collect_royalty(self, owner, key, takings):
        return 0.0


def operate(found, takings=1000.0, upkeep=100.0, wages=300.0):
    owner = Purse("firm")
    owner.adoption = None
    world = World(SimpleNamespace(takings=takings, upkeep=upkeep, wages=wages))
    business = Business()
    with mock.patch.object(business_books.adoption, "plant_weight", lambda adoption, key: 1.0), \
            mock.patch.object(business_books, "staff", lambda *arguments: found):
        margin = business_books.operate(business, owner, "shop", world, 0.0)
    return margin, owner, world, business


class OperateTests(unittest.TestCase):
    def test_the_upkeep_is_charged_once_to_suppliers_and_no_wages_are_booked_by_the_plant(self):
        _margin, owner, _world, _business = operate(1.0)
        self.assertEqual([amount for purpose, amount in owner.outlays if purpose == "upkeep"], [100.0])
        self.assertEqual([amount for purpose, amount in owner.outlays if purpose == "wages"], [])

    def test_takings_and_the_wage_bill_in_the_margin_scale_with_the_crew_found_but_the_upkeep_does_not(self):
        margin, owner, _world, business = operate(0.5)
        self.assertEqual(business.takings, 500.0)
        self.assertEqual(margin, 500.0 - 100.0 - 0.5 * 300.0)
        self.assertEqual([amount for purpose, amount in owner.outlays if purpose == "upkeep"], [100.0])

    def test_the_margin_is_takings_less_upkeep_and_wages(self):
        margin, _owner, _world, _business = operate(1.0)
        self.assertEqual(margin, 1000.0 - 100.0 - 300.0)

    def test_the_crew_found_is_noted(self):
        _margin, _owner, _world, business = operate(0.75)
        self.assertEqual(business.crew_found, 0.75)


if __name__ == "__main__":
    unittest.main()
