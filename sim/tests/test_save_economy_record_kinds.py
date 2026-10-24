"""The economy record's save, `EconomyRecord.to_record` and `EconomyRecord.from_record`, each on written-out data:
held stock in the book, term loans in the order they were struck, the state's budget, keyed stores written in id
order, tenancies and shares. (The record is stored whole under `state.economy.agent_economy["record"]`.)"""
QUICK_TOPIC = True

from sim.contracts import TERM_LOAN, Contract
from sim.economy.accounts import Book
from sim.economy.market_memory import MarketMemory
from sim.economy.record import EconomyRecord
from sim.economy.state_budget import StateBudget
from sim.economy.types import CurrencySpec, LoanRequest
from sim.tests.harness import check

COIN = CurrencySpec("coin", "fiat", None, 0.0, None)
BOOK = {"money": {"p1": {"coin": 5.0}}, "goods": {"p1": {"iron": {"t1": 4.0}}, "p0": {"iron": {"t2": 1.0}, "bread": {"t1": 2.0}}},
        "gross_money": {"coin": 5.0}, "gross_goods": {"iron": 5.0}, "money_by_purpose": {}, "goods_by_purpose": {}, "edge_money_volume": {},
        "edge_money_net": {}, "edge_goods_volume": {}, "edge_goods_net": {}, "supply_at_start": {"coin": 5.0}}


def empty_record_data():
	"""A saved record with nothing in it, as `to_record` writes it."""
	return EconomyRecord(book=Book(), memory=MarketMemory(), currency=COIN).to_record()


# ---- to_record
record = EconomyRecord(book=Book.from_record(BOOK), memory=MarketMemory(), currency=COIN)
record.loans = [Contract("loan:2", "b", "a", "coin", 25.0, rate=0.1, years_left=3.0, kind=TERM_LOAN),
                Contract("loan:1", "a", "b", "coin", 40.0, rate=0.1, years_left=2.0, arrears=5.0, kind=TERM_LOAN)]
saved = record.to_record()
check("to_record: the held stock is written by holder, then good, then tile",
      saved["book"]["goods"] == {"p0": {"bread": {"t1": 2.0}, "iron": {"t2": 1.0}}, "p1": {"iron": {"t1": 4.0}}}, saved["book"]["goods"])
check("to_record: the money and totals of the book", saved["book"]["money"] == {"p1": {"coin": 5.0}} and saved["book"]["supply_at_start"] == {"coin": 5.0}, None)
check("to_record: term loans are written in the order they were struck, not sorted by id",
      [row["contract_id"] for row in saved["loans"]] == ["loan:2", "loan:1"] and saved["loans"][1]["arrears"] == 5.0
      and saved["loans"][1]["principal"] == 40.0 and saved["loans"][1]["kind"] == TERM_LOAN, saved["loans"])
check("to_record: the currency and the empty stores", saved["currency"]["currency_id"] == "coin" and saved["producers"] == {} and saved["loan_requests"] == [], None)

record = EconomyRecord(book=Book(), memory=MarketMemory(), currency=COIN)
record.titles = {"t9": {"h_b": 0.5, "h_a": 0.5}, "t1": {"h_a": 1.0}}
record.tenancies = {"t9": [{"tenant": "x", "lessor": "y", "share": 0.2, "arrears": 0.0}], "t1": []}
record.shares = {"p_b": {"h_z": 0.1, "h_a": 0.2}, "p_a": {"h_a": 0.3}}
record.cleared_hectares = {"t5": 2.0, "t2": 1.0}
record.state_budget = StateBudget(revenue=12.0, deficit=3.0, financed={"coin": 3.0}, real_programme=True)
record.remembered_defaults = {"z": 1.0, "a": 2.0}
saved = record.to_record()
check("to_record: keyed stores are written sorted by id, however they were made",
      list(saved["titles"]) == ["t1", "t9"] and list(saved["shares"]) == ["p_a", "p_b"]
      and list(saved["shares"]["p_b"]) == ["h_a", "h_z"] and list(saved["cleared_hectares"]) == ["t2", "t5"], saved["titles"])
check("to_record: a tile's holders are kept in the order held (the outer store alone is sorted)", list(saved["titles"]["t9"]) == ["h_b", "h_a"], saved["titles"])
check("to_record: tenancies keep each tile's rows in order", saved["tenancies"]["t9"] == [{"tenant": "x", "lessor": "y", "share": 0.2, "arrears": 0.0}] and saved["tenancies"]["t1"] == [])
check("to_record: the state's budget with its financing and its flags",
      saved["state_budget"]["revenue"] == 12.0 and saved["state_budget"]["deficit"] == 3.0 and saved["state_budget"]["financed"] == {"coin": 3.0}
      and saved["state_budget"]["real_programme"] is True, saved["state_budget"])
check("to_record: stores that are plain dicts are written as they are held", saved["remembered_defaults"] == {"z": 1.0, "a": 2.0} and list(saved["remembered_defaults"]) == ["z", "a"])

# ---- from_record
data = empty_record_data()
data["book"] = BOOK
data["loans"] = [{"contract_id": "loan:2", "lender": "b", "borrower": "a", "currency": "coin", "principal": 25.0, "rate": 0.1, "years_left": 3.0,
                  "collateral_value": 0.0, "arrears": 0.0, "issued_year": 0, "arrears_interest": 0.0, "kind": "term_loan", "collateral_tile": "", "collateral_share": 0.0},
                 {"contract_id": "loan:1", "lender": "a", "borrower": "b", "currency": "coin", "principal": 40.0, "rate": 0.1, "years_left": 2.0,
                  "collateral_value": 0.0, "arrears": 5.0, "issued_year": 0, "arrears_interest": 0.0, "kind": "term_loan", "collateral_tile": "", "collateral_share": 0.0}]
built = EconomyRecord.from_record(data)
check("from_record: the held stock is in the book", built.book.stock("p1", "iron", "t1") == 4.0 and built.book.stock("p0", "bread", "t1") == 2.0
      and built.book.stock("p0", "iron", "t2") == 1.0 and built.book.stock("p0", "iron", "t1") == 0.0, None)
check("from_record: term loans are in the saved order with their arrears",
      [loan.contract_id for loan in built.loans] == ["loan:2", "loan:1"] and built.loans[1].arrears == 5.0 and built.loans[1].principal == 40.0
      and built.loans[0].lender == "b" and built.loans[0].borrower == "a", built.loans)

data = empty_record_data()
data["titles"] = {"t1": {"h_a": 1.0}, "t9": {"h_b": 0.5, "h_a": 0.5}}
data["shares"] = {"p_a": {"h_a": 0.3}, "p_b": {"h_a": 0.2, "h_z": 0.1}}
data["tenancies"] = {"t1": [], "t9": [{"tenant": "x", "lessor": "y", "share": 0.2, "arrears": 0.0}]}
data["state_budget"] = {"revenue": 12.0, "wage_budget": 0.0, "goods_budget": 0.0, "deficit": 3.0, "financed": {"coin": 3.0}, "issued_total": 0.0,
                        "unplanned_cash": 0.0, "held_back": 0.0, "need_wanted": {}, "expected_inflation": 0.0, "last_price_level": 0.0, "real_programme": True}
data["remembered_defaults"] = {"z": 1.0, "a": 2.0}
data["funds_offered"] = 7.5
data["area_imbalance"] = 1.4
data["spin_up_result"] = {"settled": True, "years": 6}
built = EconomyRecord.from_record(data)
check("from_record: keyed stores come back in the saved (id) order", list(built.titles) == ["t1", "t9"] and list(built.shares) == ["p_a", "p_b"]
      and list(built.shares["p_b"]) == ["h_a", "h_z"] and built.tenancies["t9"] == [{"tenant": "x", "lessor": "y", "share": 0.2, "arrears": 0.0}], None)
check("from_record: the state's budget is a StateBudget", built.state_budget == StateBudget(revenue=12.0, deficit=3.0, financed={"coin": 3.0}, real_programme=True), built.state_budget)
check("from_record: plain stores keep the order they were saved in", list(built.remembered_defaults) == ["z", "a"] and built.funds_offered == 7.5
      and built.area_imbalance == 1.4 and built.spin_up_result == {"settled": True, "years": 6}, None)
check("from_record: the stores the data leaves empty are empty", built.loans == [] and built.producers == {} and built.loan_requests == [] and built.currency == COIN, None)
