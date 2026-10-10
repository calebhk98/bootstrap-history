"""Complaint 110: answers to a state demand beyond comply and refuse. An actor can negotiate (a smaller sum, or a
service), conceal wealth (the state sees less to demand of), and a refusal marks it in the state's eyes. A
confiscation is a demand with an answer. Small fixtures, no whole game."""

QUICK_TOPIC = True

import random
from types import SimpleNamespace

from .harness import check

from sim.agents.api import ActorRecord, Government, Player, demand_answer
from sim.agents import demand_commands, demand_year  # noqa: F401
from sim.agents.player_commands import run_orders
from sim.engine.state_demand import answer_confiscation, answer_state_demand, set_household_stance, settle_household_year

from .agents_fake_world import FakeWorld

# ---- negotiating: a smaller sum, taken or refused ---------------------------------------------------------------
taken = demand_answer.settle_demand("negotiate", 100.0, 0.9, 0.0, 0.99)
check("an offer the state takes pays the smaller sum", taken["negotiated"] and abs(taken["paid"] - 50.0) < 1e-9, taken)
refused = demand_answer.settle_demand("negotiate", 100.0, 0.9, 0.0, 0.0)
check("an offer the state turns down pays the whole demand and no penalty",
      not refused["negotiated"] and refused["paid"] == 100.0 and refused["penalty"] == 0.0, refused)
check("negotiating is not defiance", not taken["refused"] and not refused["refused"])
check("a stronger state turns an offer down more often",
      demand_answer.negotiation_rejection_chance(0.9, 0.0, 0.5) > demand_answer.negotiation_rejection_chance(0.3, 0.0, 0.5))
check("standing makes an offer more likely to be taken",
      demand_answer.negotiation_rejection_chance(0.9, 1.0, 0.5) < demand_answer.negotiation_rejection_chance(0.9, 0.0, 0.5))
check("a state with no capacity takes any offer", demand_answer.negotiation_rejection_chance(0.0, 0.0, 0.1) == 0.0)

with_service = demand_answer.settle_demand("negotiate", 100.0, 0.9, 0.0, 0.99, service_worth=30.0)
check("a service offered stands in for part of the sum: less money, and the service is spent",
      with_service["service"] == 30.0 and abs(with_service["paid"] - 50.0) < 1e-9, with_service)
check("a service is worth less to the state than it cost, so a big one is capped at what the demand leaves",
      demand_answer.settle_demand("negotiate", 100.0, 0.9, 0.0, 0.99, service_worth=1000.0)["service"]
      <= 50.0 / demand_answer.STATE_SERVICE_VALUE_SHARE + 1e-9)
check("a service makes the offer likelier to be taken",
      demand_answer.negotiation_odds(100.0, 0.9, 0.0, 30.0)["chance_accepted"]
      > demand_answer.negotiation_odds(100.0, 0.9, 0.0, 0.0)["chance_accepted"])


class PressedWorld(FakeWorld):
    def __init__(self, capacity=0.9, draw=0.0):
        super().__init__()
        self.capacity, self.draw = capacity, draw

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


def levy_on(stance, draw, taxable=1000.0, service=0.0, capacity=0.9):
    state = Government("government:home", ActorRecord(kind="government"))
    payer = Player("player:a", ActorRecord(kind="player", money=5000.0, controller="human", demand_stance=stance,
                                            service_offer=service))
    return state.collect(payer, taxable, PressedWorld(capacity, draw)), payer, state


full, _payer, _state = levy_on("comply", 0.0)
offered, payer, state = levy_on("negotiate", 0.99)
check("a negotiated requisition is paid at the smaller sum (the office is not negotiable)",
      abs(offered - (0.5 * 200.0 + 50.0)) < 1e-9 and abs(state.money - offered) < 1e-9, offered)
insisted, _payer, _state = levy_on("negotiate", 0.0)
check("a state that insists takes the whole requisition", abs(insisted - full) < 1e-9, (insisted, full))
served, payer, state = levy_on("negotiate", 0.99, service=40.0)
check("the service is paid out of the actor's purse to the people who render it, not to the state",
      abs(state.money - served) < 1e-9 and abs(payer.money - (5000.0 - served - 40.0)) < 1e-9, (served, payer.money, state.money))
check("a negotiated requisition costs the actor less than complying", served < full)

player = Player("player:b", ActorRecord(kind="player", controller="human"))
player.record.orders.append({"command": "answer_demand", "stance": "negotiate", "service": 25})
run_orders(player, PressedWorld())
check("the command sets the stance and the service on offer",
      player.demand_stance() == "negotiate" and player.service_worth() == 25.0, player.record.journal)
check("the journal gives the odds of the offer", "chance" in player.record.journal[-1]["detail"], player.record.journal[-1])
player.record.orders.append({"command": "answer_demand", "stance": "conceal"})
run_orders(player, PressedWorld())
check("the command accepts concealing", player.demand_stance() == "conceal" and player.record.journal[-1]["ok"],
      player.record.journal[-1])

# ---- refusing marks the actor ---------------------------------------------------------------------------------------
_taken, payer, _state = levy_on("refuse", 0.99)
check("a refusal the state could not enforce still marks the actor as defiant", payer.defiance() > 0.0, payer.defiance())
_taken, payer, _state = levy_on("comply", 0.0)
check("complying leaves no mark", payer.defiance() == 0.0)
check("defiance makes the actor look larger to the state", demand_answer.notice_surcharge(0.8) > demand_answer.notice_surcharge(0.2) > 0.0)
check("with none there is no surcharge", demand_answer.notice_surcharge(0.0) == 0.0)
check("the state forgets slowly", 0.0 < demand_answer.defiance_fading(0.5) < 0.5)
check("repeated refusals cannot take defiance past one",
      max(demand_answer.defiance_after_refusal(level) for level in (0.0, 0.5, 0.9, 1.0)) <= 1.0)
check("a refusal puts blame on the one who refused and complying puts none",
      demand_answer.blame_for_refusal(True) > 0.0 and demand_answer.blame_for_refusal(False) == 0.0)

# ---- concealing wealth -----------------------------------------------------------------------------------------------
check("only an actor that conceals holds anything out of sight",
      demand_answer.concealed_target("comply", 1000.0) == 0.0 and demand_answer.concealed_target("conceal", 1000.0) > 0.0)
check("the state counts only what is not hidden", demand_answer.visible_wealth(1000.0, 400.0) == 600.0
      and demand_answer.visible_wealth(1000.0, 5000.0) == 0.0)
hidden = demand_answer.settle_concealment("conceal", 1000.0, 0.9, 0.0, 0.99)
check("wealth the state does not find stays hidden at a cost a year",
      hidden["concealed"] > 0.0 and hidden["cost"] > 0.0 and hidden["seized"] == 0.0, hidden)
found = demand_answer.settle_concealment("conceal", 1000.0, 0.9, 0.0, 0.0)
check("wealth the state finds is taken, with a penalty, and nothing stays hidden",
      found["seized"] > found["found"] > 0.0 and found["concealed"] == 0.0, found)
check("a state with no capacity cannot find it", demand_answer.settle_concealment("conceal", 1000.0, 0.0, 0.0, 0.0)["seized"] == 0.0)
check("standing makes wealth harder to find",
      demand_answer.CONCEALMENT_DETECTION_SHARE * demand_answer.enforcement_chance(0.9, 1.0)
      < demand_answer.CONCEALMENT_DETECTION_SHARE * demand_answer.enforcement_chance(0.9, 0.0))
check("an actor that stops concealing brings its wealth back",
      demand_answer.settle_concealment("comply", 1000.0, 0.9, 0.0, 0.99)["concealed"] == 0.0)


def hiding(draw, stance="conceal"):
    world = PressedWorld(0.9, draw)
    state = Government("government:home", ActorRecord(kind="government"))
    world.government_actor = state
    payer = Player("player:c", ActorRecord(kind="player", money=10000.0, controller="human", demand_stance=stance))
    return payer, state, world


payer, state, world = hiding(0.99)
demand_year.settle_year(payer, world)
check("the actor's hidden wealth is recorded and the hiding is paid for out of its purse",
      payer.concealed_wealth() > 0.0 and payer.money < 10000.0 and state.money == 0.0, (payer.concealed_wealth(), payer.money))
payer, state, world = hiding(0.0)
demand_year.settle_year(payer, world)
check("a state that finds the hoard takes it into its purse and the actor keeps nothing hidden",
      state.money > 0.0 and payer.concealed_wealth() == 0.0 and payer.money < 10000.0, (state.money, payer.money))
payer, state, world = hiding(0.99)
payer.set_demand_stance("comply")
payer.set_concealed_wealth(2000.0)
payer.set_defiance(0.5)
demand_year.settle_year(payer, world)
check("an actor that stops concealing brings the wealth back, and the state's memory of its refusals fades",
      payer.concealed_wealth() == 0.0 and 0.0 < payer.defiance() < 0.5, (payer.concealed_wealth(), payer.defiance()))

# ---- the founder's household ----------------------------------------------------------------------------------------------
class Treasury:
    def __init__(self):
        self.money = 0.0

    def credit(self, amount, purpose):
        self.money += amount


class Household(SimpleNamespace):
    def debit(self, amount, purpose):
        self.capital -= amount


def founder_game(capital=1000.0, capacity=0.9, protection=0.0, seed=1, stance="comply"):
    household = Household(demand_stance=stance, protection=protection, service_offer=0.0, concealed=0.0, defiance=0.0,
                          scandal=0.0, capital=capital, log=[])
    game = SimpleNamespace(state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=100)),
                           state_capacity=capacity, rng=random.Random(seed), treasury=Treasury(), paid_edges=[])

    def lose_capital(fraction, cause="losses", taker=None):
        lost = household.capital * fraction
        household.capital -= lost
        taker.money += lost
        return lost
    game.lose_capital = lose_capital
    game.state_treasury = lambda: game.treasury
    game.pay_edge = lambda name, amount, why: (game.paid_edges.append((name, amount)), setattr(household, "capital", household.capital - amount))
    return game


game = founder_game()
before = game.rng.getstate()
_answer, demanded, taken = answer_confiscation(game, 0.4, "confiscation")
check("a founder who complies has the confiscation taken as before, and draws no random number",
      abs(taken - 400.0) < 1e-9 and abs(demanded - 400.0) < 1e-9 and game.rng.getstate() == before, (taken, demanded))
check("the treasury receives what was taken", abs(game.treasury.money - 400.0) < 1e-9, game.treasury.money)

refusals = []
for seed in range(60):
    each = founder_game(seed=seed, stance="refuse")
    refusals.append(answer_confiscation(each, 0.4, "c") + (each,))
spared = [each for each in refusals if each[2] == 0.0]
seized = [each for each in refusals if each[2] > 0.0]
check("a refused confiscation is sometimes enforced and sometimes not", spared and seized, (len(spared), len(seized)))
check("an enforced refusal costs more than complying would have", all(each[2] > 400.0 - 1e-9 for each in seized),
      [each[2] for each in seized][:3])
check("a refusal, enforced or not, marks the household and puts blame on it",
      all(each[3].state.household.defiance > 0.0 and each[3].state.household.scandal > 0.0 for each in refusals))

negotiations = []
for seed in range(60):
    each = founder_game(seed=seed, stance="negotiate")
    negotiations.append(answer_confiscation(each, 0.4, "c"))
check("a negotiated confiscation is sometimes taken at the smaller sum",
      any(abs(each[2] - 200.0) < 1e-6 for each in negotiations), sorted({round(each[2]) for each in negotiations}))
check("and otherwise the state insists on the whole", any(abs(each[2] - 400.0) < 1e-6 for each in negotiations))

hidden_game = founder_game(seed=2, stance="conceal")
settle_household_year(hidden_game)
check("a founder who conceals has part of his capital out of the state's sight",
      hidden_game.state.household.concealed > 0.0, hidden_game.state.household.concealed)
if hidden_game.state.household.concealed > 0.0:
    _a, demanded_hidden, _t = answer_confiscation(hidden_game, 0.4, "c")
    check("the state can demand only a share of what it can see", demanded_hidden < 400.0, demanded_hidden)
check("the household's visible wealth falls by what it hides",
      demand_answer.visible_wealth(1000.0, 500.0) < demand_answer.visible_wealth(1000.0, 0.0))
note = set_household_stance(founder_game(), "negotiate", 30.0)
check("the founder's reply names the odds of the offer", "chance" in note and "service" in note, note)
note = set_household_stance(founder_game(), "conceal")
check("and of hiding wealth", "conceal" in note and "penalty" in note, note)
