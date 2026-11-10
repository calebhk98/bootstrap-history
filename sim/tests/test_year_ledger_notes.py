"""The table-backed year ledger notes a year as the dict ledger did (sim/tests/year_ledger_reference.py): the same figures, the same
keys in the same order, bit for bit. The notes are random settlements, labour results, postings, outside payments, outputs and
cleared rounds; the ledgers are compared through their dict-like attributes."""

QUICK_TOPIC = True

import random
import unittest
from collections.abc import Mapping
from types import SimpleNamespace

from sim.economy.types import ClearingResult, EDGE_MINT, Fill, GoodsMove, LabourResult, Transfer
from sim.economy.year_ledger import YearLedger

from .year_ledger_reference import ReferenceLedger

AGENTS = ["farm%d" % number for number in range(7)] + ["cohort:a", "cohort:b", EDGE_MINT, "edge:external", "edge:external:persia"]
GOODS = ["grain", "wool", "iron", "wine"]
FIGURES = ("money_out", "wages_in", "sales_in", "plant_spend", "plant_worn", "hours_sold", "spare_hours", "received", "grown",
           "hours_hired", "sold", "output", "imports_paid", "exports_received", "hours_hired_by_market", "delivered_by_market",
           "unmet_demand", "pending_mint_takes")


def shape(value):
    """A mapping as nested lists of (key, value) pairs in its order, so equality checks the order too."""
    if isinstance(value, Mapping):
        return [(key, shape(item)) for key, item in value.items()]
    return value


def settlement(rng, item, purpose, goods_sale):
    people = rng.sample(AGENTS, rng.randint(1, 8))
    count = len(people)
    amounts = lambda: [rng.choice([0.0, rng.uniform(0, 50), rng.uniform(0, 3)]) for _ in range(count)]   # noqa: E731
    keys = [(person, rng.choice(["t1", "t2"])) for person in people]
    paid, received = amounts(), amounts()
    return SimpleNamespace(
        item=item, purpose=purpose, agents=people, paid=paid, received=received, imports=amounts() if rng.random() < 0.4 else [0.0] * count,
        exports=amounts() if rng.random() < 0.4 else [0.0] * count, got_goods=[rng.random() < 0.6 for _ in people],
        goods_in=amounts(), goods_out=amounts(), keys=keys, key_to_mint=[rng.choice([0.0, 0.0, 2.5]) if goods_sale else 0.0 for _ in keys],
        paid_by={person: amount for person, amount in zip(people, paid) if amount > 0.0},
        paid_to={person: amount for person, amount in zip(people, received) if amount > 0.0})


def labour_result(rng):
    trade, area, wage = rng.choice(["plough", "mill"]), rng.choice(["north", "south"]), rng.choice([1.5, 2.0, 0.25])
    fills = tuple(Fill(person, trade, area, "", rng.uniform(1, 100), wage, rng.choice(["buy", "sell"]))
                  for person in rng.choices(AGENTS[:9], k=rng.randint(0, 7)))
    return LabourResult(trade, area, "coin", wage, 0.0, 0.0, 0.0, fills)


def clearing(rng):
    price = rng.choice([None, rng.uniform(0.5, 9)])
    return ClearingResult(rng.choice(GOODS), rng.choice(["north", "south"]), "coin", price,
                          0.0 if price is None else rng.choice([0.0, rng.uniform(0, 40)]), 0.0, 0.0, ())


def postings(rng):
    made = []
    for _ in range(rng.randint(1, 5)):
        payer, payee = rng.sample(AGENTS, 2)
        purpose = rng.choice(["sale of grain", "wages for plough", "rent", "sale of wine"])
        made.append(Transfer(payer, payee, "coin", rng.uniform(0, 30), purpose))
        if rng.random() < 0.5:
            made.append(GoodsMove(payee, payer, rng.choice(GOODS), "t1", rng.uniform(0, 9), purpose))
    return made


def note_year(rng, ledgers):
    """The same random notes into each ledger."""
    imports, exports = frozenset(["farm0"]), frozenset(["farm1"])
    plant_goods = {"farm2": {"iron"}, "farm3": {"grain", "iron"}}
    for ledger in ledgers:
        ledger.import_accounts, ledger.export_accounts = imports, exports
    for _step in range(rng.randint(5, 40)):
        action = rng.choice(["sale", "wage", "labour", "round", "postings", "outside", "wages_outside", "output", "summed", "plant", "set"])
        if action == "sale":
            done = settlement(rng, rng.choice(GOODS), "", True)
            done.purpose = "sale of " + done.item
            plant = plant_goods if rng.random() < 0.7 else None
            for ledger in ledgers:
                ledger.note_settlement(done, "sales", plant)
        elif action == "wage":
            done = settlement(rng, "plough", "wages for plough", False)
            for ledger in ledgers:
                ledger.note_settlement(done, "wages")
        elif action == "labour":
            result = labour_result(rng)
            paid_by = {fill.agent: rng.uniform(0, 200) for fill in result.fills if fill.side == "buy"}
            paid_to = {fill.agent: rng.uniform(0, 200) for fill in result.fills if fill.side == "sell"}
            settled = rng.random() < 0.7
            for ledger in ledgers:
                ledger.note_hours(result, dict(paid_by), dict(paid_to), settled)
        elif action == "round":
            result, delivered = clearing(rng), rng.uniform(0, 30)
            for ledger in ledgers:
                ledger.note_clearing(result, delivered)
        elif action == "postings":
            made, kind = postings(rng), rng.choice(["", "wages", "sales"])
            for ledger in ledgers:
                ledger.note_postings(made, kind)
        elif action in ("outside", "wages_outside"):
            made = [Transfer(*rng.sample(AGENTS, 2), "coin", rng.uniform(0, 9), "rent") for _ in range(rng.randint(0, 3))]
            for ledger in ledgers:
                getattr(ledger, "note_paid_outside_markets" if action == "outside" else "note_wages_outside_markets")(made)
        elif action == "output":
            agent, good = rng.choice(AGENTS[:7]), rng.choice(GOODS)
            moves = [GoodsMove("edge:none", agent if rng.random() < 0.8 else "farm6", good, "t1", rng.uniform(0, 20), "production") for _ in range(3)]
            for ledger in ledgers:
                ledger.note_output(agent, moves)
        elif action == "summed":
            paid = {person: rng.uniform(0, 9) for person in rng.sample(AGENTS[:9], 3)}
            income = {person: rng.uniform(0, 9) for person in rng.sample(AGENTS[:9], 3)}
            got = [((person, rng.choice(GOODS)), rng.uniform(0, 5)) for person in rng.sample(AGENTS[:9], 2)]
            foreign = [(rng.choice(["imports", "exports"]), (person, "grain"), rng.uniform(1, 5)) for person in rng.sample(AGENTS[:9], 2)]
            for ledger in ledgers:
                ledger.note_summed_sales(paid, income, got, got[:1], foreign)
        elif action == "plant":
            made = [Transfer("farm2", "farm4", "coin", 3.0, "sale of iron"), GoodsMove("farm4", "farm2", "iron", "t1", 1.0, "sale of iron")]
            for ledger in ledgers:
                ledger.note_plant_purchases(made, "iron", plant_goods)
        else:
            value, worn_agent = rng.uniform(0, 9), rng.choice(AGENTS[:5])
            for ledger in ledgers:
                ledger.plant_worn[worn_agent] = value
                ledger.spare_hours["farm0"] = value
                ledger.unmet_demand[("grain", "north")] = value


class TableLedgerNotesAsTheDictLedgerDid(unittest.TestCase):
    def test_random_years(self):
        for seed in range(80):
            rng = random.Random(seed)
            old, new = ReferenceLedger(), YearLedger()
            note_year(rng, (old, new))
            for name in FIGURES:
                self.assertEqual(shape(getattr(new, name)), shape(getattr(old, name)), "%s in year %d" % (name, seed))
            for agent in AGENTS:
                self.assertEqual(new.running_costs(agent), old.running_costs(agent))
            self.assertEqual(shape(new.market_totals()[0]), shape(old.market_totals()[0]), "market quantity in year %d" % seed)
            self.assertEqual(shape(new.market_totals()[1]), shape(old.market_totals()[1]), "market price in year %d" % seed)

    def test_reads_in_the_middle_of_a_year_see_the_notes_so_far(self):
        for seed in range(20):
            rng = random.Random(1000 + seed)
            old, new = ReferenceLedger(), YearLedger()
            for _step in range(6):
                note_year(rng, (old, new))
                for name in ("money_out", "sold", "hours_hired", "output"):
                    self.assertEqual(shape(getattr(new, name)), shape(getattr(old, name)))

    def test_a_read_adds_only_the_notes_its_table_waits_on(self):
        ledger = YearLedger()
        ledger.note_output("farm0", [GoodsMove("edge:none", "farm0", "grain", "t1", 4.0, "production")])
        ledger.note_settlement(settlement(random.Random(1), "grain", "sale of grain", True), "sales")
        pending = ledger.tables.pending
        self.assertEqual(ledger.output[("farm0", "grain")], 4.0)
        self.assertEqual((pending.counts[0] > 0, pending.counts[3]), (True, 0))       # the settlement still waits; the output is in
        ledger.money_out.get("farm0")
        self.assertEqual(pending.counts[0], 0)


if __name__ == "__main__":
    unittest.main()
