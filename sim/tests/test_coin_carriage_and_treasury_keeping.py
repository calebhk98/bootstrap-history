"""Complaint 273: coin moved across a route pays carriage by its mass, and a state's or firm's coin pays the
yearly keeping cost the household's does."""
from .harness import *  # noqa: F401,F403
from functools import partial

from sim.engine.data import load_civ
from sim.engine.state import ActorRecord
from sim.engine.coin_hoard import KEEPING_CAUSE

sim = partial(sim, agent_economy=False)

PARTNER = "han_china_100ad"
COIN = load_civ(PARTNER)["coin_standard"]


def settled(carriage_per_tonne, flow_tonnes):
    """(partner coin units after one settlement, the ledger) with coin carriage at the stated money a tonne."""
    game = sim(civ="rome_100ad", capital=1e9)
    game.foreign_economies = lambda: [PARTNER]
    game._coin_carriage_money_per_tonne = lambda civilization_id: carriage_per_tonne
    per_coin = COIN["kg_per_unit"] * game._material_prices()[COIN["material"]]
    value = 0.05 * game.home_coin_stock_units() * per_coin
    before = game._foreign_ledger(PARTNER)["partner_coin_units"]
    game._settle_flow(PARTNER, flow_tonnes, value, per_coin)
    ledger = game._foreign_ledger(PARTNER)
    return ledger["partner_coin_units"] - before, ledger, value / per_coin


free_received, free_ledger, owed_units = settled(0.0, 5.0)
dear_received, dear_ledger, _owed = settled(2000.0, 5.0)
check("with free carriage the partner receives the whole payment", abs(free_received - owed_units) < 1e-6 * owed_units,
      (free_received, owed_units))
check("coin carried over a route pays carriage by its mass, so the partner receives less",
      0.0 < dear_received < free_received, (dear_received, free_received))
check("the carriage paid is recorded in coin units", dear_ledger["coin_carriage_units"] > 0.0
      and abs(dear_ledger["coin_carriage_units"] - (free_received - dear_received)) < 1e-6 * owed_units, dear_ledger)
dearer_received, _ledger, _owed = settled(4000.0, 5.0)
check("dearer carriage takes more of the coin", free_received - dearer_received > 1.9 * (free_received - dear_received),
      (dearer_received, dear_received))


def coin_total_change(carriage_per_tonne, flow_tonnes):
    """(change in payer + receiver + carriers' coin in home money, carriage booked) over one settlement."""
    game = sim(civ="rome_100ad", capital=1e9)
    game.foreign_economies = lambda: [PARTNER]
    game._coin_carriage_money_per_tonne = lambda civilization_id: carriage_per_tonne
    per_coin = COIN["kg_per_unit"] * game._material_prices()[COIN["material"]]
    game._settle_flow(PARTNER, flow_tonnes, 0.05 * game.home_coin_stock_units() * per_coin, per_coin)
    ledger = game._foreign_ledger(PARTNER)
    return ledger["home_coin_units"] + ledger["partner_coin_units"] * per_coin, ledger["coin_carriage_units"]


for direction, flow in (("an import", 5.0), ("an export", -5.0)):
    total, carriage = coin_total_change(2000.0, flow)
    check("carriers are paid, so %s settlement leaves the total coin unchanged" % direction,
          carriage > 0.0 and abs(total) <= 1e-9 * carriage * COIN["kg_per_unit"] * 1e6, (total, carriage))

# --- any actor holding coin pays to keep it.


def keeping_paid(treasury_money, firm_money):
    """(the state's, a firm's) outlay on keeping coin after one year of actors."""
    game = sim(civ="rome_100ad", capital=1e6, manual=False, events=False)
    treasury = game.state_treasury()
    treasury.money = treasury_money
    firm = game.actors.add("firm:coin_keeper", ActorRecord(kind="firm", name="coin keeper", money=firm_money))
    game.advance_actors(game.state.scenario.year)
    cause = KEEPING_CAUSE
    return treasury.record.outlays.get(cause, 0.0), firm.record.outlays.get(cause, 0.0)


poor_state, poor_firm = keeping_paid(1.0e3, 1.0e3)
rich_state, rich_firm = keeping_paid(1.0e8, 1.0e8)
check("a state's treasury is charged for keeping its coin", rich_state > 0.0, rich_state)
check("a larger treasury is charged more", rich_state > poor_state > 0.0, (poor_state, rich_state))
check("a firm holding coin is charged the same way", rich_firm > poor_firm > 0.0, (poor_firm, rich_firm))
