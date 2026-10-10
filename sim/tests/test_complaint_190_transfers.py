"""Complaint 190: a one-off transfer to the state (its debt, the claims it owes interest groups, relief), usable by
a work that declares `transfer` and by the `pay` command, and a state's share of one concern's takings."""
from .harness import *  # noqa: F401,F403

from sim.agents.api import ledger
from sim.agents.api import ActorRecord


class _Succeeds(random.Random):
    def random(self):
        return 0.999


def indebted(owed, capital=1.0e9):
    """A game whose state owes `owed` and whose household holds `capital`, the economy left unopened."""
    game = unopened_sim(capital=capital)
    ledger.transfer(game.state_treasury(), game.edge("edge:state_spending"), owed, "spend")
    return game


# ---- paying the state's debt: the household's loss is the treasury's gain -------------------------
game = indebted(5000.0)
before = game.state.household.capital
paid, said = game.settle_with_state("debt")
check("paying the debt moves exactly what the state owed from the household to the treasury",
      paid == 5000.0 and game.state_debt() == 0.0 and abs(before - game.state.household.capital - 5000.0) < 1e-6,
      (paid, game.state_debt(), before, game.state.household.capital))
check("the reply says the state owes nothing now", "owes nothing" in said, said)

poor = indebted(5000.0, capital=1200.0)
paid, said = poor.settle_with_state("debt")
check("a household that cannot cover the debt pays what it has and the rest stays owed",
      paid == 1200.0 and poor.state_debt() == 3800.0 and poor.state.household.capital == 0.0
      and "still owes" in said, (paid, poor.state_debt(), poor.state.household.capital, said))

nothing = unopened_sim(capital=1.0e6)
paid, said = nothing.settle_with_state("debt")
check("a state that owes nothing is not paid for nothing", paid == 0.0 and nothing.state.household.capital == 1.0e6, (paid, said))

gift = indebted(1000.0)
paid, said = gift.settle_with_state(None, 4000.0)
check("a sum past the debt clears it and leaves the rest in the state's purse as a reserve",
      paid == 4000.0 and gift.state_debt() == 0.0 and gift.state_treasury().money == 3000.0,
      (paid, gift.state_debt(), gift.state_treasury().money))

# ---- the claims the state owes interest groups ------------------------------------------------------
claimed = unopened_sim(capital=1.0e9)
claimed.actors.add("group:test", ActorRecord(kind="interest_group", claim=700.0, group_kind="displaced_producers",
                                              subject="iron", name="producers of iron", cause="your sales"))
check("the claims the state has undertaken are counted", claimed.state_claims() == 700.0, claimed.state_claims())
purse = claimed.state_treasury().money
paid, said = claimed.settle_with_state("claims")
check("paying the claims puts them in the state's purse, where its budget funds the groups from",
      paid == 700.0 and claimed.state_treasury().money == purse + 700.0, (paid, purse, claimed.state_treasury().money))

# ---- a work that declares `transfer` pays when it is finished ------------------------------------------
for node_id, base in (("ben_state_debt_redemption", "debt"), ("ben_political_settlement", "claims"),
                      ("ben_disaster_relief_grant", None)):
    check("%s declares a transfer" % node_id, "transfer" in (NODES[node_id].get("mechanics") or {}), node_id)
    check("%s is knowledge once done, not a going concern with upkeep" % node_id, NODES[node_id]["up"] == 0, NODES[node_id]["up"])

redeem = indebted(8000.0, capital=1.0e9)
redeem.rng = _Succeeds(1)
redeem.done.update(NODES["ben_state_debt_redemption"]["pre"])
redeem._done_changed()
redeem.initialize_project("ben_state_debt_redemption")
capital_before = redeem.state.household.capital
redeem._complete("ben_state_debt_redemption")
check("finishing the redemption pays the state's whole debt",
      "ben_state_debt_redemption" in redeem.done and redeem.state_debt() == 0.0, redeem.state_debt())
check("the household is poorer by the debt (and the work's own cost)",
      capital_before - redeem.state.household.capital >= 8000.0 - 1e-6, (capital_before, redeem.state.household.capital))
check("the log says what was paid", any("paid the state" in text for _year, text in redeem.state.household.log),
      redeem.state.household.log[-3:])

relief = unopened_sim(capital=1.0e12)
relief.rng = _Succeeds(1)
relief.done.update(NODES["ben_disaster_relief_grant"]["pre"])
relief._done_changed()
relief.initialize_project("ben_disaster_relief_grant")
purse = relief.state_treasury().money
relief._complete("ben_disaster_relief_grant")
sized = NODES["ben_disaster_relief_grant"]["mechanics"]["transfer"]["labour_hours"] * relief.labour.money_per_labour_hour()
check("a relief grant is a stated sum of labour hours priced in the society's coin",
      abs(relief.state_treasury().money - purse - sized) < 1e-3 * sized, (relief.state_treasury().money - purse, sized))

# a work never pays the state into debt: the purse is the limit
short = unopened_sim(capital=1.0e12)
short.rng = _Succeeds(1)
short.done.update(NODES["ben_disaster_relief_grant"]["pre"])
short._done_changed()
short.initialize_project("ben_disaster_relief_grant")
short.state.household.capital = 10.0
short._complete("ben_disaster_relief_grant")
check("a work pays no more than the household has: it empties the purse and does not run into debt",
      short.state.household.capital == 0.0, short.state.household.capital)

# ---- the pay command ---------------------------------------------------------------------------------
commanded = indebted(2500.0)
reply = S._agent_dispatch(commanded, NODES, {"cmd": "pay", "what": "debt"})
check("`pay state debt` pays and says how much", reply.get("ok") and reply["paid"] == 2500.0 and reply["state_debt"] == 0.0, reply)
reply = S._agent_dispatch(commanded, NODES, {"cmd": "pay", "what": "debt"})
check("a second payment of a debt that is gone is refused and changes nothing", reply.get("ok") is False, reply)
reply = S._agent_dispatch(commanded, NODES, {"cmd": "pay", "amount": 100.0})
check("`pay state <amount>` pays a stated sum", reply.get("ok") and reply["paid"] == 100.0, reply)
reply = S._agent_dispatch(commanded, NODES, {"cmd": "pay"})
check("`pay` with nothing named is refused", reply.get("ok") is False, reply)

from sim.ui.proto.typed import parse_typed

check("the typed line `pay state debt` reads", parse_typed("pay state debt")[0] == {"cmd": "pay", "what": "debt"}, parse_typed("pay state debt"))
check("the typed line `pay state 500` reads", parse_typed("pay state 500")[0] == {"cmd": "pay", "amount": 500.0}, parse_typed("pay state 500"))
check("the typed line `pay state claims` reads", parse_typed("pay claims")[0] == {"cmd": "pay", "what": "claims"}, parse_typed("pay claims"))

# ---- the state's share of one concern's takings ------------------------------------------------------
for node_id in ("fin_gambling_house", "fin_lottery"):
    levy = (NODES[node_id].get("mechanics") or {}).get("state_levy")
    check("%s pays the state a share of its takings" % node_id, bool(levy) and 0.0 < levy["share"] < 1.0, levy)
check("a state lottery gives the state a larger share than a private gambling house",
      NODES["fin_lottery"]["mechanics"]["state_levy"]["share"] > NODES["fin_gambling_house"]["mechanics"]["state_levy"]["share"])

levied = unopened_sim(capital=1.0e9)
levied.done.add("fin_gambling_house")
levied._done_changed()
levied.state.projects.operating.add("fin_gambling_house")
levied.state.projects.opened_year["fin_gambling_house"] = levied.state.scenario.year - 100
# the market's room for the output is the agent economy's answer; one open concern's takings are what is measured
levied.node_output_market_factor = lambda node: 1.0
due = levied.concern_levy_due()
takings = levied.concern_revenue("fin_gambling_house") * levied.state.economy.output_factor
check("an open gambling house owes the state its share of what it earns",
      takings > 0 and abs(due.get("fin_gambling_house", 0.0) - 0.1 * takings) < 1e-6 * takings, (due, takings))
purse, capital = levied.state_treasury().money, levied.state.household.capital
levied.pay_concern_levies(levied.state.scenario.year)
check("the levy moves from the household to the treasury",
      abs(levied.state_treasury().money - purse - due["fin_gambling_house"]) < 1e-6
      and abs(capital - levied.state.household.capital - due["fin_gambling_house"]) < 1e-6,
      (levied.state_treasury().money - purse, capital - levied.state.household.capital))
check("a closed concern owes nothing", unopened_sim().concern_levy_due() == {})
