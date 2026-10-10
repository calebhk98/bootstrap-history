"""Import and export duties are assessed on the money the year's postings moved through the external edge."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import taxes
from sim.economy.accounts import Book
from sim.economy.types import EDGE_EXTERNAL, EDGE_MINT, Transfer, external_edge
from sim.economy.year_close import tax_facts
from sim.economy.year_ledger import YearLedger


def facts_after(*postings, imports=(), exports=()):
    book = Book()
    book.transfer(Transfer(EDGE_MINT, "merchant", "coin", 1000.0, "opening"))
    book.transfer(Transfer(EDGE_MINT, "weaver", "coin", 100.0, "opening"))
    ledger = YearLedger(import_accounts=frozenset(imports), export_accounts=frozenset(exports))
    for transfer in postings:
        book.transfer(transfer)
        ledger.note_postings([transfer], "sales")
    setup = types.SimpleNamespace(currency_id="coin", working_hours_per_year=2000.0, unskilled_trade="labour",
                                  countries=lambda: ["home"])
    record = types.SimpleNamespace(book=book, cohorts={})
    return tax_facts(setup, record, types.SimpleNamespace(wage=lambda *_args: 0.0), ledger)


class ForeignDutyTests(unittest.TestCase):
    def test_an_import_payment_owes_the_import_duty(self):
        facts = facts_after(Transfer("merchant", EDGE_EXTERNAL, "coin", 200.0, "sale of silk"))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("customs", "imports_value", 0.1),), facts,
                                                       "state", {})
        self.assertEqual([(each.payer, each.amount) for each in transfers], [("merchant", 20.0)])

    def test_an_export_receipt_owes_the_export_duty(self):
        facts = facts_after(Transfer(EDGE_EXTERNAL, "weaver", "coin", 50.0, "sale of cloth"))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("outward", "exports_value", 0.2),), facts,
                                                       "state", {})
        self.assertEqual([(each.payer, each.amount) for each in transfers], [("weaver", 10.0)])

    def test_a_payment_to_one_partners_edge_owes_the_import_duty(self):
        facts = facts_after(Transfer("merchant", external_edge("han"), "coin", 200.0, "sale of silk"))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("customs", "imports_value", 0.1),), facts,
                                                       "state", {})
        self.assertEqual([(each.payer, each.amount) for each in transfers], [("merchant", 20.0)])

    def test_the_sale_of_a_landed_cargo_owes_the_import_duty(self):
        facts = facts_after(Transfer("weaver", "merchant", "coin", 60.0, "sale of silk"), imports=("merchant",))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("customs", "imports_value", 0.1),), facts,
                                                       "state", {})
        self.assertEqual([(each.payer, round(each.amount, 9)) for each in transfers], [("merchant", 6.0)])

    def test_a_sale_by_an_account_that_landed_nothing_owes_no_duty(self):
        facts = facts_after(Transfer("weaver", "merchant", "coin", 60.0, "sale of silk"))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("customs", "imports_value", 0.1),), facts,
                                                       "state", {})
        self.assertEqual(transfers, [])

    def test_the_purchase_of_a_cargo_for_abroad_owes_the_export_duty(self):
        facts = facts_after(Transfer("merchant", "weaver", "coin", 50.0, "sale of cloth"), exports=("merchant",))
        transfers, _moves, _assessments = taxes.assess((taxes.TaxForm("outward", "exports_value", 0.2),), facts,
                                                       "state", {})
        self.assertEqual([(each.payer, each.amount) for each in transfers], [("merchant", 10.0)])


if __name__ == "__main__":
    unittest.main()
