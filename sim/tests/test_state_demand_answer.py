"""Complaint 110: an actor the state presses answers the demand (comply or refuse), and what a refusal
costs follows from the state's capacity and the actor's standing. Small fixtures, no whole game."""

QUICK_TOPIC = True

from .harness import check

from sim.agents.api import ActorRecord, Government, Player
from sim.agents import demand_answer, demand_commands  # noqa: F401  (demand_commands registers the command)
from sim.agents.player_commands import run_orders

from .agents_fake_world import FakeWorld


# ---- the pure answer ------------------------------------------------------------------------
complied = demand_answer.settle_demand("comply", 100.0, 0.9, 0.0, 0.0)
check("complying pays the demand and nothing more", complied["paid"] == 100.0 and complied["penalty"] == 0.0, complied)
check("an unknown stance is treated as compliance, never as a free pass",
      demand_answer.settle_demand("", 100.0, 0.9, 0.0, 0.0)["paid"] == 100.0)

lucky = demand_answer.settle_demand("refuse", 100.0, 0.5, 0.0, 0.99)
check("a refusal the state fails to enforce pays nothing", lucky["paid"] == 0.0 and lucky["withheld"] == 100.0, lucky)
caught = demand_answer.settle_demand("refuse", 100.0, 0.5, 0.0, 0.01)
check("a refusal the state enforces pays the demand and a penalty",
      caught["enforced"] and caught["paid"] > 100.0 and caught["penalty"] == caught["paid"] - 100.0, caught)

strong = demand_answer.enforcement_chance(0.9, 0.0)
weak = demand_answer.enforcement_chance(0.2, 0.0)
check("a more capable state enforces more often", strong > weak > 0.0, (strong, weak))
check("a state with no capacity never enforces", demand_answer.enforcement_chance(0.0, 0.0) == 0.0)
check("standing turns part of the enforcement aside",
      demand_answer.enforcement_chance(0.9, 1.0) < strong, demand_answer.enforcement_chance(0.9, 1.0))
check("standing never makes a capable state wholly powerless",
      demand_answer.enforcement_chance(0.9, 1.0) > 0.0)
check("an enforced refusal against a stronger state costs more",
      demand_answer.settle_demand("refuse", 100.0, 0.9, 0.0, 0.0)["penalty"]
      > demand_answer.settle_demand("refuse", 100.0, 0.3, 0.0, 0.0)["penalty"])
check("a state with no capacity takes a refusal as final",
      demand_answer.settle_demand("refuse", 100.0, 0.0, 0.0, 0.0)["paid"] == 0.0)

odds = demand_answer.refusal_odds(100.0, 0.9, 0.0)
check("the odds a player is shown agree with the settlement",
      odds["chance_enforced"] == strong and odds["pay_if_enforced"] == demand_answer.settle_demand(
          "refuse", 100.0, 0.9, 0.0, 0.0)["paid"] and odds["pay_if_complying"] == 100.0, odds)

# ---- the government levies an actor by its stance ---------------------------------------------
class PressedWorld(FakeWorld):
	def __init__(self, capacity=0.9, draw=0.0):
		super().__init__()
		self.capacity = capacity
		self.draw = draw

	def state_capacity(self):
		return self.capacity

	def visible_scale_of(self, actor):
		return 1.0

	def levy_shares(self, scale, protection=0.0):
		return 0.2, 0.05

	def rng_for(self, *parts):
		world = self

		class Roll:
			def random(self):
				return world.draw
		return Roll()


def levy_on(stance, capacity=0.9, draw=0.0, taxable=1000.0):
	state = Government("government:home", ActorRecord(kind="government"))
	payer = Player("player:a", ActorRecord(kind="player", money=5000.0, controller="human", demand_stance=stance))
	taken = state.collect(payer, taxable, PressedWorld(capacity, draw))
	return taken, payer, state


compliant, _payer, _state = levy_on("comply")
check("an actor that complies pays requisition and office as before", abs(compliant - 250.0) < 1e-9, compliant)
refused, payer, state = levy_on("refuse", draw=0.99)
check("a refusal the state does not enforce pays the office but not the requisition",
      abs(refused - 50.0) < 1e-9 and abs(payer.money - 4950.0) < 1e-9, (refused, payer.money))
enforced, payer, state = levy_on("refuse", draw=0.0)
check("a refusal the state enforces costs more than complying",
      enforced > compliant, (enforced, compliant))
weak_state, _payer, _state = levy_on("refuse", capacity=0.0, draw=0.0)
check("a state without capacity cannot enforce a refusal", abs(weak_state - 50.0) < 1e-9, weak_state)
check("the state's purse receives what was taken", abs(state.money - enforced) < 1e-9, state.money)

# ---- the command, for any actor the state presses ---------------------------------------------
player = Player("player:b", ActorRecord(kind="player", controller="human"))
check("an actor answers demands by complying until it says otherwise", player.demand_stance() == "comply")
player.record.orders.append({"command": "answer_demand", "stance": "refuse"})
run_orders(player, PressedWorld())
check("the command sets the stance", player.demand_stance() == "refuse", player.record.journal)
check("the journal gives the odds of the refusal",
      "chance" in player.record.journal[-1]["detail"] and player.record.journal[-1]["ok"], player.record.journal)
player.record.orders.append({"command": "answer_demand", "stance": "pretend"})
run_orders(player, PressedWorld())
check("a stance not built yet is refused and the old one stands",
      not player.record.journal[-1]["ok"] and player.demand_stance() == "refuse", player.record.journal[-1])

# ---- the founder's household answers the same way ---------------------------------------------
import random
from types import SimpleNamespace

from sim.engine.state_demand import answer_state_demand, set_household_stance


def founder_game(capacity=0.9, protection=0.0, seed=1):
	return SimpleNamespace(state=SimpleNamespace(household=SimpleNamespace(demand_stance="comply", protection=protection, service_offer=0.0, concealed=0.0, defiance=0.0, scandal=0.0)),
	                       state_capacity=capacity, rng=random.Random(seed))


game = founder_game()
before = game.rng.getstate()
check("a founder who complies pays the demand without touching the random stream",
      answer_state_demand(game, 100.0)["paid"] == 100.0 and game.rng.getstate() == before)
note = set_household_stance(game, "refuse")
check("the founder's stance is set and the reply names the odds",
      game.state.household.demand_stance == "refuse" and "chance" in note, note)
outcomes = [answer_state_demand(game, 100.0) for _roll in range(200)]
caught = [each for each in outcomes if each["enforced"]]
check("across many demands a refusing founder is sometimes enforced and sometimes not",
      0 < len(caught) < len(outcomes), len(caught))
check("the share enforced follows the state's capacity",
      abs(len(caught) / len(outcomes) - demand_answer.enforcement_chance(0.9, 0.0)) < 0.12, len(caught))
protected = founder_game(protection=1.0)
protected.state.household.demand_stance = "refuse"
caught_protected = sum(answer_state_demand(protected, 100.0)["enforced"] for _roll in range(200))
check("a protected founder is enforced against less often", caught_protected < len(caught), (caught_protected, len(caught)))
try:
	set_household_stance(game, "hide")
	rejected = False
except ValueError:
	rejected = True
check("a stance not built yet is rejected for the founder too", rejected and game.state.household.demand_stance == "refuse")
