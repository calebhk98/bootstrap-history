"""Complaint 315: some forms are paid in kind and arrive as goods in the state's stores, to be used or sold through
the goods market. Complaint 640: one played year of a state taking grain in kind (wiring of revenue, stores, dole and
the granary's sale); the forms and their bases are test_state_revenue_forms and the granary rules are in test_state_works."""
from .harness import *  # noqa: F401,F403

sim = unopened_sim   # legacy: pins surplus grain sold into the engine's goods market, which the agent economy does not run


from sim.engine.agents_port import SimWorld
from sim.agents import authority, budget_lines
from sim.agents.tuning_spending import GRANARY_LOSS_SHARE_PER_YEAR

HARVEST_KG = 4.0e9


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def declared(game, forms):
    game.state_treasury().record.revenue_forms = list(forms)   # the state's own forms, copied from the file at setup
    return SimWorld(game)


LAND = {"form": "land_tax", "basis": "harvest", "rate": 0.1, "paid_in": "wheat_kg"}

# ---- in-kind revenue arrives as goods and goes through the goods market ---------------------------
kind = sim()
kind.state.holdings.farm_last_harvest_kg = HARVEST_KG
treasury = kind.state_treasury()
treasury.money = 0.0
kind_world = declared(kind, [LAND])
due = 0.1 * HARVEST_KG / 1000.0
# what the officials keep of what they collect is never the state's (authority.py), so the stores get the tithe less it
kept = next(assessed.kept_by_officials for assessed in kind_world.revenue_assessments() if assessed.form == "land_tax")
tithe = authority.after_leakage(due, kept)
granary_target = 0.5 * tithe   # a reserve smaller than the harvest, so some grain is above it
treasury.granary_target = lambda world: granary_target
offered = []   # (seller, material, tonnes) the state puts to the agent economy's book
real_note_sale = kind.economy.note_actor_sale
kind.economy.note_actor_sale = lambda seller, material, tonnes, from_concerns: (
    offered.append((seller, material, tonnes)), real_note_sale(seller, material, tonnes, from_concerns))[1]
one_year(kind)
check("the officials keep a share of the tithe, and not all of it", 0.0 < kept < authority.OFFICIAL_KEEP_CEILING, kept)
check("a share of the harvest taken in kind is recorded as goods received, in tonnes",
      abs(treasury.record.in_kind_received.get("wheat_kg", 0.0) - tithe) < 1e-6 * tithe,
      treasury.record.in_kind_received)
check("in-kind revenue is not booked as coin taxation", treasury.record.income.get("taxation", 0.0) == 0.0,
      treasury.record.income)
check("the revenue by form is recorded in money's worth, for the audit",
      treasury.record.revenue_by_form.get("land_tax", 0.0) > 0.0, treasury.record.revenue_by_form)
commodity = SimWorld(kind).commodity_of("wheat_kg")
dole = budget_lines.dole_line(SimWorld(kind))[0].materials[commodity]
sold = sum(tonnes for seller, material, tonnes in offered if seller == treasury.actor_id and material == "wheat_kg")
bought = kind._market_flows()["bought"].get(commodity, {}).get(treasury.actor_id, 0.0)
check("grain the dole needs comes out of the stores, so the state buys none of it", bought == 0.0, (bought, dole))
held_before_sale = (tithe - dole) * (1.0 - GRANARY_LOSS_SHARE_PER_YEAR)
check("grain above the granary's target is sold into the goods market and the target is kept",
      sold > 0.0 and abs(sold - (held_before_sale - granary_target)) < 1e-6 * tithe
      and 0.0 < treasury.record.stores.get("wheat_kg", 0.0) <= granary_target,
      (sold, dole, treasury.record.stores, tithe, granary_target))
# the proceeds reach the purse when the agent economy's year clears the book (test_economy_agent_state.py)
check("the purse still equals income less outlays",
      abs(treasury.money - (sum(treasury.record.income.values()) - sum(treasury.record.outlays.values())))
      < 1e-6 * abs(treasury.record.income.get("sale of stores", 1.0)), treasury.money)
