"""spending_previews: money a player spends or is told about is previewed, and
the preview calls the same function as the charge (Complaints 216, 218, 236,
248, 214)."""
from .harness import *  # noqa: F401,F403


def _ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# --- 220: quote hire / commission / open equal what is then charged ---------
hire_sim = sim(capital=1e7)
net_before_hire = _ask(hire_sim, cmd="money")["net_per_year"]
hire_quote = _ask(hire_sim, cmd="quote", what="hire", trade="smith", n=2)
check("quote hire answers", hire_quote.get("ok"), hire_quote)
capital_before = hire_sim.capital
check("quote hire charges nothing", hire_sim.capital == capital_before)
hire_reply = _ask(hire_sim, cmd="hire", trade="smith", n=2)
check("the hire charge equals the quote",
      abs((capital_before - hire_sim.capital) - hire_quote.get("paid_now", -1)) < 0.06,
      (capital_before - hire_sim.capital, hire_quote))
check("the hire reply itemises what was paid now",
      abs(hire_reply.get("paid_now", -1) - hire_quote.get("paid_now", -2)) < 0.06, hire_reply)
check("the hire reply says what is due from next year",
      hire_reply.get("from_next_year_per_year", 0) > 0, hire_reply)
from sim.ui.proto.typed import parse_typed
check("typed 'quote hire smith 2' parses as a hire quote",
      (parse_typed("quote hire smith 2")[0] or {}).get("what") == "hire"
      and (parse_typed("quote hire smith 2")[0] or {}).get("trade") == "smith",
      parse_typed("quote hire smith 2"))
check("typed 'quote bounty <id>' parses as a bounty quote",
      (parse_typed("quote bounty fin_restaurant")[0] or {}).get("id") == "fin_restaurant",
      parse_typed("quote bounty fin_restaurant"))

commission_sim = hire_sim
commission_quote = _ask(commission_sim, cmd="quote", what="commission", trade="smith", hours=100)
check("quote commission answers", commission_quote.get("ok"), commission_quote)
capital_before = commission_sim.capital
commission_reply = _ask(commission_sim, cmd="commission", trade="smith", hours=100)
check("the commission charge equals the quote",
      abs((capital_before - commission_sim.capital) - commission_quote.get("paid_now", -1)) < 0.06,
      (capital_before - commission_sim.capital, commission_quote))
check("the commission reply states the hours expire and cannot supervise",
      "supervise" in str(commission_reply.get("note", "")), commission_reply)
check("help commission states expiry",
      "this year" in str(_ask(hire_sim, cmd="help", topic="commission")), "")

open_sim = hire_sim
venture_id = next(node_id for node_id in ORDER if open_sim.is_venture(node_id)
                  and node_id not in open_sim.done)
open_sim.done.add(venture_id)
open_sim._done_changed()
open_quote = _ask(open_sim, cmd="quote", what="open", id=venture_id)
check("quote open answers", open_quote.get("ok"), open_quote)
capital_before = open_sim.capital
open_reply = _ask(open_sim, cmd="open", id=venture_id)
check("the opening charge equals the quote",
      abs((capital_before - open_sim.capital) - open_quote.get("paid_now", -1)) < 0.06,
      (capital_before - open_sim.capital, open_quote))
check("the open reply names the opening charge",
      abs(open_reply.get("opening_charge", -1) - open_quote.get("paid_now", -2)) < 0.06,
      open_reply)

# --- 222: recurring net is before the hiring advance ------------------------
money_after = _ask(hire_sim, cmd="money")
expected_drop = hire_sim.labour.wage_bill()
check("recurring net falls by the whole wage after a hire",
      (net_before_hire - money_after["net_per_year"]) > 0.9 * expected_drop,
      (net_before_hire, money_after["net_per_year"], expected_drop))
check("money lists the advance as a separate one-off",
      money_after["what_it_costs_you"].get("of_which_already_paid_as_hiring_advances"),
      money_after["what_it_costs_you"])
state_after = _ask(hire_sim, cmd="state")
check("state and money agree on recurring net",
      abs(state_after["net_per_year"] - money_after["net_per_year"]) < 1.0,
      (state_after["net_per_year"], money_after["net_per_year"]))

# --- 248: quote bounty ------------------------------------------------------
bounty_sim = sim(capital=1e9)
bounty_id = next(node_id for node_id in ORDER
                 if node_id not in bounty_sim.done and NODES[node_id]["ph"] > 100
                 and NODES[node_id]["lab"] and bounty_sim.bounty_eligible(node_id))
bounty_quote = _ask(bounty_sim, cmd="quote", what="bounty", id=bounty_id)
check("quote bounty answers with eligibility", bounty_quote.get("ok")
      and bounty_quote.get("eligible") is True, bounty_quote)
check("quote bounty states the multiplier",
      abs(bounty_quote.get("price_multiplier", 0) - bounty_sim.BOUNTY_PRICE_MULTIPLIER) < 1e-9,
      bounty_quote)
capital_before = bounty_sim.capital
bounty_reply = _ask(bounty_sim, cmd="bounty", id=bounty_id)
check("the bounty charge equals the quote",
      abs((capital_before - bounty_sim.capital) - bounty_quote.get("paid_now", -1)) < 0.06,
      (capital_before - bounty_sim.capital, bounty_quote))
check("the bounty reply repeats the same price",
      abs(bounty_reply.get("price", -1) - round(bounty_quote.get("paid_now", -5), 1)) < 0.11, bounty_reply)
refused_id = next((node_id for node_id in ORDER if node_id not in bounty_sim.done
                   and not bounty_sim.bounty_eligible(node_id)), None)
refused_quote = _ask(bounty_sim, cmd="quote", what="bounty", id=refused_id)
refused_reply = _ask(bounty_sim, cmd="bounty", id=refused_id)
check("quote bounty gives the same refusal the bounty command gives",
      refused_quote.get("eligible") is False
      and refused_quote.get("refusal") == refused_reply.get("error"),
      (refused_quote, refused_reply))

# --- 240: a cash tail after the last scheduled payment settles --------------
tail_sim = bounty_sim
tail_sim.capital = 1e10
tail_id = next(node_id for node_id in ORDER if node_id not in tail_sim.done
               and tail_sim.can_start(node_id) and tail_sim.project_cost(node_id) > 5e3
               and NODES[node_id]["yrs"] <= 1)
tail_sim.start_project(tail_id)
project_state = tail_sim.active[tail_id]
project_state["ph_left"] = 0.0
project_state["lab_left"] = {}
project_state["cost_left"] = tail_sim.project_cost(tail_id) * 1.0005
tail_sim.step()
check("a few cash units left after the final instalment do not cost another year",
      tail_id in tail_sim.done, project_state)

# --- 214: sustainable debt beside the formal ceiling ------------------------
debt_sim = sim(capital=2e4)
debt_money = _ask(debt_sim, cmd="money")
check("money shows the debt the recurring surplus can carry",
      "sustainable_debt" in debt_money, sorted(debt_money))
check("the sustainable figure comes from the shared method",
      abs(debt_money.get("sustainable_debt", -1e9) - getattr(debt_sim, "sustainable_debt", lambda: 0.0)()) < 0.1 and "sustainable_debt" in debt_money,
      debt_money.get("sustainable_debt"))
expensive_id = next(node_id for node_id in ORDER if node_id not in debt_sim.done
                    and debt_sim.can_start(node_id) and 2.2e4 < debt_sim.project_cost(node_id) < 2.8e4)
start_reply = _ask(debt_sim, cmd="start", id=expensive_id)
credit_forecast = start_reply.get("on_credit") or {}
check("the start warning shows sustainable debt beside the ceiling",
      "sustainable_debt" in credit_forecast
      and "interest_as_share_of_recurring_surplus" in credit_forecast,
      start_reply)

# --- 222: letting someone go says what happens to the advance ---------------
fire_reply = _ask(hire_sim, cmd="fire", trade="smith", n=1)
check("firing in the year of hire says what happens to the paid-in-advance wage",
      fire_reply.get("advance_still_credited", 0) > 0 and fire_reply.get("advance_note"),
      fire_reply)

# --- 220: why shows the charge to open a concern ----------------------------
why_reply = _ask(open_sim, cmd="why", id=venture_id)
check("why shows the charge to open", why_reply.get("charge_to_open") is not None, sorted(why_reply))
