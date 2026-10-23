"""Complaint 314: soldiers are a trade in the one labour market. The state's army is people of that trade
at its wage, conscription moves the wage, and soldiers taken out of the unskilled pool make unskilled
labour scarcer. Complaint 640: each rule is called on inputs built here (a budget over a stand-in world, a labour market
over a stub labour, the state's hiring over a fake world); no game is played."""
QUICK_TOPIC = True

import types

from .harness import check

from sim.agents import budget
from sim.agents.api import Government
from sim.agents.budget_line import Line
from sim.agents.records import ActorRecord
from sim.labour import trade_data
from sim.labour.labour_market_api import LabourMarket
from sim.labour.labour_population import PopulationMixin

from .agents_fake_world import FakeWorld

SOLDIER_WAGE = 800.0
HOURS = 2000.0


# ---- the army is people of the soldier trade at its wage ---------------------------------------------
class ArmyWorld(FakeWorld):
    def pay_per_person_year(self, trade):
        return SOLDIER_WAGE if trade == "soldier" else 500.0

    def equipment_kg_per_soldier(self):
        return 20.0

    def commodity_of(self, material):
        return material

    def material_cost(self, material, tonnes):
        return 3.0 * tonnes


army = budget.army_line(ArmyWorld(), 1000.0)[0]
check("the army is people of the soldier trade, not labourers", set(army.labour) == {"soldier"}, army.labour)
check("army pay is the soldier trade's wage in the one labour market",
      abs(army.wages - 1000.0 * SOLDIER_WAGE) < 1e-6 * army.wages, army.wages)
conscripted = budget.army_line(ArmyWorld(), 1000.0, 400.0)[0]
check("conscripts serve a labour due and draw no pay", abs(conscripted.wages - 600.0 * SOLDIER_WAGE) < 1e-6 and conscripted.labour == {"soldier": 600.0},
      conscripted)

# ---- soldiers come from the whole working age, as unskilled labour does -------------------------------
WORKING_AGE = 1.0e6
labour_world = types.SimpleNamespace(
    population=types.SimpleNamespace(total=4.0e6, working_age=WORKING_AGE), civ={"urban_fraction": 0.1}, urban_fraction=lambda: 0.1,
    literacy=lambda field: 0.1)
population = types.SimpleNamespace(trade_available=lambda trade: True, _world=labour_world)
check("a trade drawn from the unskilled pool has the whole working age to call on",
      PopulationMixin.national_trade_population(population, "soldier") == WORKING_AGE)
check("soldier is a trade drawn from the unskilled pool", trade_data.drawn_from_unskilled_pool("soldier"))
absent = types.SimpleNamespace(trades_absent=set(), state=None)
check("soldier is a trade the labour market can supply here",
      PopulationMixin.trade_available(types.SimpleNamespace(_world=absent), "soldier"))


# ---- the state's soldiers press the labour market ----------------------------------------------------
class SoldierMarket(LabourMarket):
    """A labour market over a stub labour whose standing staff are `soldiers`; its quote is not under test."""

    def __init__(self, soldiers=0.0, supply=WORKING_AGE * HOURS):
        state = types.SimpleNamespace(household=types.SimpleNamespace(labour_pressure_records={}),
                                      scenario=types.SimpleNamespace(year=100))
        world = types.SimpleNamespace(
            state=state, HOURS_PER_PERSON_YEAR=HOURS, wages={"labourer": 1.0, "soldier": 1.0, "smith": 1.0},
            trade_registry={"labourer": {"fallback": True}, "soldier": {}, "smith": {}},
            actor_staff_fte=lambda trade: soldiers if trade == "soldier" else 0.0)
        labour = types.SimpleNamespace(_world=world, market_supply=lambda trade: supply,
                                       wage_schedule=lambda: types.SimpleNamespace(training_years={}))
        super().__init__(labour)

    def quote(self, trade, hours=0.0, employer=None, pay_premium=0.0):
        return 0.0


idle = SoldierMarket()
small, large = SoldierMarket(soldiers=0.02e6), SoldierMarket(soldiers=0.2e6)
check("with no army the unskilled trade carries no standing draw", idle.pressure("labourer") == 0.0)
check("soldiers under arms are drawn from the unskilled pool, so unskilled labour is leaned on",
      small.pressure("labourer") == 0.02e6 * HOURS, small.pressure("labourer"))
check("with a fifth of the working age under arms, unskilled labour costs more",
      large.price_factor("labourer") > idle.price_factor("labourer"), (large.price_factor("labourer"), idle.price_factor("labourer")))
check("a larger army raises it further", large.price_factor("labourer") > small.price_factor("labourer") > idle.price_factor("labourer"))
check("the soldiers' own trade is not leaned on by the standing draw", large.pressure("soldier") == 0.0)

before = idle.price_factor("soldier")
idle.hire(None, "soldier", 0.002e6 * HOURS)
modest = idle.price_factor("soldier")
bigger = SoldierMarket()
bigger.hire(None, "soldier", 0.2e6 * HOURS)
check("soldiers hired by the state raise the soldier wage", modest > before, (modest, before))
check("a larger levy raises it further", bigger.price_factor("soldier") > modest, (bigger.price_factor("soldier"), modest))


# ---- the state hires its soldiers through that market -----------------------------------------------------
class HiringWorld(FakeWorld):
    def local_staff(self, trade, people):
        return people


state = Government("government:home", ActorRecord(kind="government"))
world = HiringWorld()
held = dict(state.workforce)
state.employ_standing([Line("army", "requisition", {"soldier": 1000.0}, 1000.0 * SOLDIER_WAGE)], 1.0, world)
check("the state's soldiers are in its workforce under their own trade", state.workforce.get("soldier") == 1000.0, state.workforce)
state.press_new_staff(held, world)
check("the state presses the labour market for the soldiers it took on, in hours",
      world.labour_market.hired == {"soldier": 1000.0 * world.hours_per_person_year}, world.labour_market.hired)
state.employ_standing([Line("army", "requisition", {"soldier": 1000.0}, 1000.0 * SOLDIER_WAGE)], 0.5, world)
check("a part-funded army takes on only the funded share", state.workforce["soldier"] == 1500.0, state.workforce)
