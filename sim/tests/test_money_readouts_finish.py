"""money_readouts_finish: each preview and the action it previews call one
function for the amount (Complaints 261, 216, 236, 210, 240, 212)."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.render_screen_state import render_state
from sim.ui.proto.render_screens_economy import render_money
from sim.ui.proto.state_waiting import _waiting_on


def _ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# --- 265: the available AFFORD column and row marks use the start rule ------
for debt in (0, -3000, -6000):
    debtor = sim(civ="rome_100ad", capital=5000)
    debtor.state.household.capital = debt
    startable = [node_id for node_id in NODES if node_id not in debtor.done
                 and node_id not in debtor.active and debtor.start_reason(node_id)[0]]
    payable = {node_id for node_id in startable if debtor.start_refusal(node_id) is None}
    digest = _ask(debtor, cmd="available")
    if "subjects" in digest:
        check("AFFORD column totals the starts `start` accepts (capital %s)" % debt,
              sum(row["you_could_pay_for"] for row in digest["subjects"]) == len(payable),
              (sum(row["you_could_pay_for"] for row in digest["subjects"]), len(payable)))
    listing = _ask(debtor, cmd="available", all=True)
    marked = {entry["id"] for entry in listing["available"] if entry.get("cannot_pay_now")}
    check("rows `start` refuses are marked cannot_pay_now (capital %s)" % debt,
          marked == set(startable) - payable,
          (len(marked), len(startable) - len(payable)))

# --- 220: quote train previews what train then charges and the wage bill ----
train_sim = sim(capital=1e8)
train_quote = _ask(train_sim, cmd="quote", what="train", trade="machinist", n=1)
check("quote train answers", train_quote.get("ok"), train_quote)
check("quote train states the wage bill the trainee adds",
      train_quote.get("wage_bill_added_per_year", 0) > 0, train_quote)
capital_before = train_sim.capital
check("quote train charges nothing", train_sim.capital == capital_before)
train_reply = _ask(train_sim, cmd="train", trade="machinist", n=1)
check("the training charge equals the quote",
      abs((capital_before - train_sim.capital) - train_quote.get("paid_now", -1)) < 0.06,
      (capital_before - train_sim.capital, train_quote))
check("the train reply repeats the wage bill to come",
      abs(train_reply.get("wage_bill_added_per_year", -1)
          - train_quote.get("wage_bill_added_per_year", -2)) < 0.06, train_reply)
too_many = _ask(sim(capital=1e8), cmd="quote", what="train", trade="machinist", n=500)
check("quote train refuses more than the household can take and changes nothing",
      too_many.get("ok") is False and too_many.get("error"), too_many)
from sim.ui.proto.typed import parse_typed
check("typed 'quote train machinist 2' parses as a train quote",
      (parse_typed("quote train machinist 2")[0] or {}).get("what") == "train",
      parse_typed("quote train machinist 2"))

# --- 240: waiting_on names what is short ------------------------------------
waiting_sim = sim(capital=1e9)
calendar_id = next(node_id for node_id in ORDER if NODES[node_id]["yrs"] >= 3
                   and not NODES[node_id]["lab"])
calendar_text = _waiting_on(waiting_sim, NODES, calendar_id,
                            {"ph_left": 0.0, "yrs": 1.0, "lab_left": {}}, 0.0)
check("waiting_on on the calendar says how many years are left",
      calendar_text.startswith("the calendar")
      and str(int(NODES[calendar_id]["yrs"]) - 1) in calendar_text, calendar_text)
hours_text = _waiting_on(waiting_sim, NODES, calendar_id,
                         {"ph_left": 1234.0, "yrs": 0.0, "lab_left": {}}, 0.0)
check("waiting_on on hours says how many are still needed",
      "1,234" in hours_text, hours_text)

# --- 214: state carries the sustainable debt --------------------------------
debt_sim = sim(capital=1e6)
debt_sim.state.household.capital = -50000
state_reply = _ask(debt_sim, cmd="state")
check("state carries the sustainable debt, the same figure money shows",
      state_reply.get("sustainable_debt") == round(debt_sim.sustainable_debt(), 1)
      and _ask(debt_sim, cmd="money").get("sustainable_debt") == state_reply.get("sustainable_debt"),
      state_reply.get("sustainable_debt"))
check("the state screen prints a sustainable debt line when in arrears",
      "ustainable debt" in render_state(state_reply), "")

# --- 244: a mine quote prices the running cost the new working will be charged
mine_sim = sim(civ="han_china_100ad", capital=1e12)
mine_sim.state.economy.mines = [{"material": "coal", "capacity": 500.0, "opened_year": 100,
                                 "capex_paid": 0.0,
                                 "intensity_yrs": mine_sim.DEPLETION_HALF_LIFE_YRS * 0.5}]
mine_quote = mine_sim.mine_quote("coal", 100)
new_working = {"material": "coal", "capacity": 100.0, "opened_year": 103,
               "capex_paid": 0.0, "intensity_yrs": 0.0}
check("the mine quote's yearly cost is what the new working is charged",
      abs(mine_quote["every_year_it_stands"] - mine_sim.mine_operating_cost_for(new_working))
      < 0.06, (mine_quote["every_year_it_stands"], mine_sim.mine_operating_cost_for(new_working)))

# --- 216: the market deduction is itemised by category ----------------------
absorb_sim = sim(civ="rome_100ad", capital=1e9)
earners = [node_id for node_id in ORDER if absorb_sim.is_venture(node_id)
           and NODES[node_id]["rev"] > 0][:12]
run_it(absorb_sim, *earners)
absorb_sim.REVENUE_CEILING_PER_POP_SCALE = 1000.0
absorb_sim.household._revenue_cache_key = None
sources = absorb_sim.revenue_sources()
deduction = -sources.get("_what_the_market_will_not_absorb", 0.0)
check("the setup has a market deduction to itemise", deduction > 1.0, sources)
money_reply = _ask(absorb_sim, cmd="money")
squeeze = money_reply.get("where_the_market_squeeze_falls") or []
check("money itemises the deduction by category", len(squeeze) >= 1, money_reply.keys())
check("the category rows sum to the deduction",
      abs(sum(row["lost"] for row in squeeze) - deduction) < 0.2,
      (sum(row["lost"] for row in squeeze), deduction))
check("each category row names its concerns and what was nominal and absorbed",
      all(row.get("concerns") and row["nominal"] >= row["absorbed"] for row in squeeze), squeeze)
check("the money screen prints the itemised deduction",
      "by category" in render_money(money_reply), "")
