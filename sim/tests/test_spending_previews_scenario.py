"""Scenarios in a whole game: money a player spends or is told about is previewed, and the preview calls the same function as
the charge (Complaints 216, 218, 220, 222, 236, 240, 248, 214). The typed lines and the tail rule are in
test_spending_previews."""
from .harness import *  # noqa: F401,F403


def _ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


# --- 220, 248: quote hire / commission / open / bounty equal what is then charged
hire_sim = unopened_sim(capital=1e7)
net_before_hire = _ask(hire_sim, cmd="money")["net_per_year"]
capital_before_quote = hire_sim.capital
hire_quote = _ask(hire_sim, cmd="quote", what="hire", trade="smith", n=2)
capital_before = hire_sim.capital
check("quote hire answers and charges nothing", hire_quote.get("ok") and capital_before == capital_before_quote, hire_quote)
hire_reply = _ask(hire_sim, cmd="hire", trade="smith", n=2)
check("the hire charge equals the quote and the hire reply itemises it, with what is due from next year",
      abs((capital_before - hire_sim.capital) - hire_quote.get("paid_now", -1)) < 0.06
      and abs(hire_reply.get("paid_now", -1) - hire_quote.get("paid_now", -2)) < 0.06
      and hire_reply.get("from_next_year_per_year", 0) > 0, (capital_before - hire_sim.capital, hire_quote, hire_reply))

commission_quote = _ask(hire_sim, cmd="quote", what="commission", trade="smith", hours=100)
capital_before = hire_sim.capital
commission_reply = _ask(hire_sim, cmd="commission", trade="smith", hours=100)
check("the commission charge equals the quote",
      commission_quote.get("ok") and abs((capital_before - hire_sim.capital) - commission_quote.get("paid_now", -1)) < 0.06,
      (capital_before - hire_sim.capital, commission_quote))
# presentation: the commission reply and its help say the hours expire
check("the commission reply and its help state that the hours expire and cannot supervise",
      "supervise" in str(commission_reply.get("note", "")) and "this year" in str(_ask(hire_sim, cmd="help", topic="commission")),
      commission_reply)

venture_id = next(node_id for node_id in ORDER if hire_sim.is_venture(node_id) and node_id not in hire_sim.done)
hire_sim.done.add(venture_id)
hire_sim._done_changed()
open_quote = _ask(hire_sim, cmd="quote", what="open", id=venture_id)
capital_before = hire_sim.capital
open_reply = _ask(hire_sim, cmd="open", id=venture_id)
check("the opening charge equals the quote, the open reply names it and why shows it",
      open_quote.get("ok") and abs((capital_before - hire_sim.capital) - open_quote.get("paid_now", -1)) < 0.06
      and abs(open_reply.get("opening_charge", -1) - open_quote.get("paid_now", -2)) < 0.06
      and _ask(hire_sim, cmd="why", id=venture_id).get("charge_to_open") is not None,
      (capital_before - hire_sim.capital, open_quote, open_reply))

bounty_sim = sim(capital=1e9)
bounty_id = next(node_id for node_id in ORDER
                 if node_id not in bounty_sim.done and NODES[node_id]["ph"] > 100
                 and NODES[node_id]["lab"] and bounty_sim.bounty_eligible(node_id))
bounty_quote = _ask(bounty_sim, cmd="quote", what="bounty", id=bounty_id)
capital_before = bounty_sim.capital
bounty_reply = _ask(bounty_sim, cmd="bounty", id=bounty_id)
refused_id = next((node_id for node_id in ORDER if node_id not in bounty_sim.done and not bounty_sim.bounty_eligible(node_id)), None)
refused_quote = _ask(bounty_sim, cmd="quote", what="bounty", id=refused_id)
refused_reply = _ask(bounty_sim, cmd="bounty", id=refused_id)
check("the bounty charge equals the quote, the reply repeats the price, and a refused bounty gives the quote's refusal",
      bounty_quote.get("ok") and bounty_quote.get("eligible") is True
      and abs(bounty_quote.get("price_multiplier", 0) - bounty_sim.BOUNTY_PRICE_MULTIPLIER) < 1e-9
      and abs((capital_before - bounty_sim.capital) - bounty_quote.get("paid_now", -1)) < 0.06
      and abs(bounty_reply.get("price", -1) - round(bounty_quote.get("paid_now", -5), 1)) < 0.11
      and refused_quote.get("eligible") is False and refused_quote.get("refusal") == refused_reply.get("error"),
      (bounty_quote, bounty_reply, refused_quote, refused_reply))

# --- 222: recurring net is before the hiring advance, and letting someone go says what happens to the advance
money_after = _ask(hire_sim, cmd="money")
state_after = _ask(hire_sim, cmd="state")
check("recurring net falls by the whole wage after a hire, the advance is a separate one-off, and state and money agree",
      (net_before_hire - money_after["net_per_year"]) > 0.9 * hire_sim.labour.wage_bill()
      and money_after["what_it_costs_you"].get("of_which_already_paid_as_hiring_advances")
      and abs(state_after["net_per_year"] - money_after["net_per_year"]) < 1.0,
      (net_before_hire, money_after["net_per_year"], hire_sim.labour.wage_bill()))
fire_reply = _ask(hire_sim, cmd="fire", trade="smith", n=1)
check("firing in the year of hire says what happens to the paid-in-advance wage",
      fire_reply.get("advance_still_credited", 0) > 0 and fire_reply.get("advance_note"), fire_reply)

# --- 240: the sliver left after the final instalment settles in the step that finishes the project
tail_sim = bounty_sim
tail_sim.capital = 1e10
tail_id = max((node_id for node_id in ORDER if node_id not in tail_sim.done
               and tail_sim.can_start(node_id) and NODES[node_id]["yrs"] <= 1),
              key=lambda node_id: (tail_sim.project_cost(node_id), node_id))   # the dearest one-year project: the sliver is largest
tail_sim.start_project(tail_id)
project_state = tail_sim.active[tail_id]
project_state["ph_left"] = 0.0
project_state["lab_left"] = {}
project_state["cost_left"] = tail_sim.project_cost(tail_id) * 1.0005
tail_sim.step()
check("a few cash units left after the final instalment do not cost another year", tail_id in tail_sim.done, project_state)

# --- 214: sustainable debt beside the formal ceiling
debt_sim = unopened_sim(capital=2e4)
debt_sim.market_credit_room = lambda actor_id: None    # the household's own standing sets the line; the opening's loan book is fully lent to others
debt_money = _ask(debt_sim, cmd="money")
check("money shows the debt the recurring surplus can carry, from the shared method",
      abs(debt_money.get("sustainable_debt", -1e9) - debt_sim.sustainable_debt()) < 0.1, debt_money.get("sustainable_debt"))
expensive_id = max((node_id for node_id in ORDER if node_id not in debt_sim.done and debt_sim.can_start(node_id)
                    and debt_sim.project_cost(node_id) < 0.5 * debt_sim.funding_capacity()),
                   key=lambda node_id: (debt_sim.project_cost(node_id), node_id))
# the materials are bought from cash at the start, so the cash held must cover them and fall short of the instalments
probe_sim = unopened_sim(capital=2e4)
probe_sim.capital = 100 * probe_sim.project_cost(expensive_id)
probe_reply = _ask(probe_sim, cmd="start", id=expensive_id)
debt_sim.capital = probe_reply["of_which_materials_paid_now"] + 0.5 * probe_reply["of_which_instalments_still_owed"]
credit_forecast = _ask(debt_sim, cmd="start", id=expensive_id).get("on_credit") or {}
check("the start warning shows sustainable debt beside the ceiling",
      "sustainable_debt" in credit_forecast and "interest_as_share_of_recurring_surplus" in credit_forecast, credit_forecast)
