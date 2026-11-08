"""The keep of the bonded as a table: one row per bonded stratum, one row per owner, and the kernel that decides, in row order, which
payments the owner's purse covers outright.

A keeper (the owner of a bonded stratum) pays the bonded's food for the year to the bonded stratum. Each payment draws the owner's
purse down, so a later row sees what the earlier rows left. The kernel keeps that draw-down order: a row is `covered` when the
owner's purse, as the earlier covered rows left it, holds the whole payment. A row that is not covered (the purse is short, so the
payment would take back a deposit or draw on the facility, which are contracts in the book) and every later row of the same owner
are paid by the Python rule `ledger.pay_up_to`, which the boundary (`keep_boundary.py`) calls: the facility is the contracts' own
lever, so it stays a Python call. An owner that is itself paid in the same call is not followed at all (its purse changes where the
kernel does not see it)."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec
from sim.jit import njit

KEEPS = TableSpec("Keeps", (
    Column("owner", numpy.int64, "the keeper's row in the owners table", "owner number"),
    Column("members", numpy.float64, "people in the bonded stratum", "people"),
    Column("cost_per_person", numpy.float64, "the year's food for one person at the year's prices", "currency units per person-year"),
    Column("allowance", numpy.float64, "keep already paid for the year", "currency units"),
    Column("labour_product", numpy.float64, "the bonded's product handed to the owner before the keep is paid (0 when none)", "currency units"),
    Column("top_up", numpy.int8, "1: pay only what the food costs beyond the allowance; 0: pay the whole cost", "flag"),
    Column("due", numpy.float64, "what the row pays, 0 when it pays nothing", "currency units"),
    Column("covered", numpy.int8, "1 when the owner's purse, as the earlier covered rows left it, holds `due`", "flag"),
))
Keeps = KEEPS.make_type(__name__)

OWNERS = TableSpec("KeepOwners", (
    Column("purse", numpy.float64, "what the owner's account holds in the book (its facility and deposit are not counted)", "currency units"),
    Column("known", numpy.int8, "1 while the kernel can follow this owner's purse; 0 once a payment fell to the Python rule, or if the owner is paid in this call", "flag"),
))
KeepOwners = OWNERS.make_type(__name__)

DUST = 1e-9   # a payment at or below this moves no money in the book (sim.book DEBT_FLOOR); it is noted and costs the purse nothing


@njit
def keep_due(members, cost_per_person, allowance, top_up):
    """What one row pays: the whole cost of the year's food, or (when topping up) the part of it beyond the allowance; 0 when nothing is owed."""
    cost = members * cost_per_person
    if top_up == 0:
        return cost
    shortfall = cost - allowance
    return shortfall if shortfall > 0.0 else 0.0


@njit
def plan_keeps(keeps, owners):
    """Fill `due` and `covered` of every row in row order. A positive payment is covered while its owner is followed and its purse holds
    the whole of it; the purse then falls by it. The first payment that is not covered ends the following of that owner (`known` = 0).
    The labour product an owner receives before its row's payment raises the purse the same way. Reads every column, writes `due`,
    `covered` and the owners' columns."""
    for row in range(keeps.row_count[0]):
        owner = keeps.owner[row]
        keeps.due[row] = keep_due(keeps.members[row], keeps.cost_per_person[row], keeps.allowance[row], keeps.top_up[row])
        keeps.covered[row] = 0
        if owners.known[owner] == 0:
            continue
        if keeps.labour_product[row] > 0.0:
            owners.purse[owner] += keeps.labour_product[row]
        due = keeps.due[row]
        if due <= 0.0:
            continue
        if due <= DUST:
            keeps.covered[row] = 1
        elif owners.purse[owner] >= due:
            keeps.covered[row] = 1
            owners.purse[owner] -= due
        else:
            owners.known[owner] = 0
