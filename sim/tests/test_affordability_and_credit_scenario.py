"""SCENARIO (affordability and credit): in a whole game spending_power is the one rule every cash gate (hire, train, commission,
open, start) asks, auto_open says why it refuses, the credit line warns before it is crossed, the arrears banner quotes
the ledger, an insolvency announces the reputation it took, and a part-paid project keeps what was paid when credit is
withdrawn. The rules on built numbers are in test_affordability_and_credit."""
from .harness import *  # noqa: F401,F403
from sim.refusal import cause_of, facts_of
from sim.engine import affordability
from .agent_command_helpers import pristine_game


def reset_overrides(game, *names):
    """Drop the instance-level overrides a check installed, restoring the class methods."""
    for name in names or ("credit_limit", "spending_power", "project_cost"):
        game.__dict__.pop(name, None)


def spending_power_spy(game, forced=None):
    """Record every kind spending_power is asked for; `forced` makes it answer that number, so a
    site's own decision can be driven by a number the test controls."""
    calls = []
    real = game.spending_power

    def spy(kind):
        calls.append(kind)
        return real(kind) if forced is None else forced
    game.spending_power = spy
    return calls


# --- scenario: auto_open says why it refuses, and in deep arrears opens only what pays for its own door
opener = sim(capital=1.0)
best_concern = max((node_id for node_id in NODES if NODES[node_id]["rev"] > NODES[node_id]["up"] > 0),
                   key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
opener.done.add(best_concern)
opener._done_changed()
opened = opener.auto_open_ventures()
refused_and_said = (best_concern not in opened
                    and any(best_concern in message for _, message in opener.log))

# A completed, earning concern that pays for its door within months opens even deep in arrears;
# a slow one and an institution do not.
# (the nodes that earn from their output; the payback is the engine's own: capex over net earnings)
paybacks = {node_id: affordability.payback_years(opener.venture_capex(node_id), node["rev"], node["up"])
            for node_id, node in opener.nodes.items()
            if node["rev"] > node["up"] and opener.is_venture(node_id)
            and sum(opener.venture_hands(node_id)) <= opener.FOUNDER_IS_WORTH   # staffed by the founder alone
            and opener.venture_foreman(node_id)[0] is None}
# deep in arrears is past half the credit line but still inside it, so a door fee can still be raised
def into_arrears(game):
    game.credit_limit = lambda: 1.0e6
    game.capital = -0.6 * game.credit_limit()


# the quickest earning concern and the slowest (the rule itself is checked above on built numbers); the line is
# made wide so the door fee can be raised and only the payback gate decides
quick_payback = min(paybacks, key=lambda node_id: (paybacks[node_id], node_id))
slow_payback = max(paybacks, key=lambda node_id: (paybacks[node_id], node_id))
assert paybacks[quick_payback] < opener.AUTO_OPEN_PAYBACK_LIMIT_YEARS < paybacks[slow_payback], paybacks
deep = sim()
deep.done.add(quick_payback)
deep._done_changed()
into_arrears(deep)
deep_in_the_red = deep.capital < 0 and -deep.capital > deep.credit_limit() * 0.5
quick_opens = quick_payback in deep.auto_open_ventures()
deep.done.add(slow_payback)
deep._done_changed()
into_arrears(deep)
deep.log.clear()
opened_slow = deep.auto_open_ventures()
slow_refusal_named = any("pay for its own doors" in message and "clear enough debt" in message for _, message in deep.log)
deep.done.add("workshop_first")
deep._done_changed()
institution_stays_shut = "workshop_first" not in deep.auto_open_ventures()
past_line = opener
past_line.done.add(quick_payback)
past_line._done_changed()
past_line.state.household.capital = -3.0 * past_line.credit_limit()
nothing_past_the_line = (past_line.spending_power("open") == 0.0 and quick_payback not in past_line.auto_open_ventures())
# presentation: the refusal names its own payback period and what would clear it
check("scenario: auto_open opens nothing it cannot pay the capex on and says why; deep in arrears a concern that pays for "
      "its own door within months still opens, a slow one stays shut with a refusal naming its payback and what would "
      "clear it, an institution opens nothing, and nothing opens once the debt is past the credit line",
      refused_and_said and deep_in_the_red and quick_opens and slow_payback not in opened_slow and slow_refusal_named
      and institution_stays_shut and nothing_past_the_line,
      (refused_and_said, deep_in_the_red, quick_opens, opened_slow, slow_refusal_named, institution_stays_shut,
       nothing_past_the_line))

# --- scenario: a fresh game's affordability screens, credit warning, job and patron
fresh = sim()
fresh.market_credit_room = lambda actor_id: None    # the household's own standing sets the line; the opening's loan book is fully lent to others
fresh_start_power = fresh.spending_power("start")
available_reply = S._agent_dispatch(fresh, NODES, {"cmd": "available"})
hint = str((available_reply.get("to_see_more") or {}).get("what you can pay for", ""))
money_reply = S._agent_dispatch(fresh, NODES, {"cmd": "money"})
thin_credit_limit = fresh.credit_limit()
starting_capital = fresh.capital
fresh.log.clear()
fresh.capital = -fresh.credit_limit() * 0.75
fresh.warn_near_the_limit(105)
near_limit_lines = [message for _, message in fresh.log]
fresh.capital = starting_capital
# A lender does not cut your line because you took a job this year.
fresh.wage_hours_this_year = fresh.labour.director_pool()
line_with_job = fresh.credit_limit()
fresh.wage_hours_this_year = 0.0
# A grand friend does not lend more than income can carry.
fresh.done.add("patron_senatorial")
fresh._done_changed()
# presentation: the hint prints the start rule's figure; the warning names what could still be done
check("scenario: in a fresh game the AFFORD hint uses the rule `start` uses, the ledger says how much of the credit line "
      "is used, the founder with a practice can still just reach a cover identity, the line warns before it is crossed "
      "naming what could be done, a job this year does not cut the line, and a grand friend lends no more than income carries",
      str(int(fresh_start_power)).replace(",", "") in hint.replace(",", "")
      and money_reply.get("of_that_limit_you_have_used") is not None
      and fresh.capital + thin_credit_limit >= fresh.project_cost("identity_cover")
      and any(cause_of(message) == "credit_near_limit" and "stop" in message and "mothball" in message for message in near_limit_lines)
      and abs(line_with_job - thin_credit_limit) < 1e-6
      and fresh.credit_limit() < thin_credit_limit * 3
      and fresh.credit_limit() * fresh.debt_interest_rate() < fresh.revenue(),
      (hint, money_reply.get("of_that_limit_you_have_used"), near_limit_lines[:1], thin_credit_limit, line_with_job,
       fresh.credit_limit()))

# --- scenario: the arrears banner quotes what the ledger does
arrears = sim(capital=-4000.0)
arrears.insolvent_years = 20
arrears.revenue = lambda: 0.0
arrears.market_rate = lambda: 0.08   # a settled market may clear at zero; the banner is about a rate that costs
diagnosis = arrears.stall_diagnosis()
ledger_loss = (arrears.revenue() - arrears.upkeep() - arrears.living_cost() - arrears.mine_operating_cost()
               - max(0.0, -arrears.capital) * arrears.debt_interest_rate())
# presentation: the banner quotes the ledger's loss and names the interest part
check("scenario: the arrears banner quotes the same loss the ledger does and names the part of it that is interest on the "
      "arrears themselves",
      diagnosis and "{:,.0f}".format(-ledger_loss) in diagnosis["you_are_stuck"]
      and any("interest on the arrears" in reason for reason in diagnosis["what_would_change_it"]),
      (diagnosis or {}).get("you_are_stuck"))

# A founder whose standing job pays nothing: wage work is advised when it pays more than the standing job already
# sells those hours for (a founder holding no trade has no standing job to beat).
wage_game = sim(civ="norse_900ad", capital=-40000.0)
wage_game.revenue = wage_game.revenue_capacity = lambda: 0.0
wage_game.held_trade = lambda: None
wage_game.insolvent_years = 20
wage_advice = [reason for reason in (wage_game.stall_diagnosis() or {}).get("what_would_change_it", [])
               if reason.startswith("work as a ")]
# The advice's quote is what work_for_wages pays for the trade and hours it names.
quote_match = re.match(r"work as a (\w+): (\d+) of your own hours .* bring in about ([\d,]+)",
                       wage_advice[0]) if wage_advice else None
advice_holds = False
advice_detail = wage_advice
if quote_match:
    quoted_trade, quoted_hours = quote_match.group(1), int(quote_match.group(2))
    quoted_earning = int(quote_match.group(3).replace(",", ""))
    capital_before = wage_game.capital
    paid, refusal = wage_game.labour.work_for_wages(quoted_trade, quoted_hours)
    advice_holds = (refusal is None and abs(paid - quoted_earning) <= 1
                    and abs((wage_game.capital - capital_before) - paid) < 1e-6
                    and quoted_trade == wage_game.labour.best_wage_trade())
    advice_detail = (quoted_earning, paid, wage_game.capital - capital_before, quoted_trade, wage_game.labour.best_wage_trade())

# A founder whose standing job already sells the hours is advised wage work only for the gain over that job, and
# the banner names what the job pays for them.
job_game = sim(civ="norse_900ad", capital=-40000.0)
job_game.revenue = job_game.revenue_capacity = lambda: 0.0
job_game.held_trade = lambda: "labourer"
job_game.insolvent_years = 20
job_advice = [reason for reason in (job_game.stall_diagnosis() or {}).get("what_would_change_it", [])
              if reason.startswith("work as a ")]
standing_pay = job_game.labour.standing_job_pay("labourer")
check("scenario: a stalled household in debt is offered wage work whose quote is what the work pays, naming the trade that "
      "pays most an hour; a founder with a standing job is offered only the gain over it, naming what that job pays",
      advice_holds and job_advice and "{:,.0f}".format(standing_pay) in job_advice[0], (advice_detail, job_advice, standing_pay))

# --- scenario: an idle fortune bleeds living costs, and the ledger names the part that is wealth
rich_ledger = S._agent_dispatch(sim(capital=hours_money(20200000)), NODES, {"cmd": "money"})
check("scenario: the ledger names the part of your living costs that is your wealth",
      (rich_ledger.get("what_it_costs_you") or {}).get("_of_which_because_you_are_rich", 0) > 1000,
      rich_ledger.get("what_it_costs_you"))

# --- scenario: refusals and quotes in debt, on one game whose capital and credit line are set per case
debtor = sim(capital=0.0)


def set_position(capital, credit_limit=None):
    reset_overrides(debtor)
    debtor.capital = capital
    if credit_limit is not None:
        debtor.credit_limit = lambda: credit_limit


debtor.capital = 400.0
game_buy, game_start = debtor.spending_power("buy"), debtor.spending_power("start")
quote_reply = S._agent_dispatch(debtor, NODES, {"cmd": "quote", "what": "mine", "material": "coal", "n": 500})
check("scenario: the game's spending_power is the one rule, and quote counts the credit a lender would actually advance",
      abs(game_buy - (400.0 + debtor.credit_limit() * 0.5)) < 1e-6 and abs(game_start - (400.0 + debtor.credit_limit())) < 1e-6
      and quote_reply.get("you_could_raise", 0) > quote_reply.get("you_have", 0), (game_buy, game_start, quote_reply.get("you_could_raise")))

# hire/train/commission may draw only half the credit line; the refusal says which rule and why.
set_position(-50000.0)
hire_ok, hire_message = debtor.labour.hire("smith", 3)
hire_fee = debtor.labour.hire_fee("smith", 3)
train_ok, train_message = debtor.labour.train("machinist", 1, None)   # one trainee: the hours fit, so cash is what refuses
commission_ok, commission_message = debtor.labour.commission("smith", 3500.0)
# presentation: the refusal's explanation of the lending rule
check("scenario: a cash-short hire, train and commission are refused with the same reasoning: which rule (half the credit "
      "line, not all of it), why (a lender funds work under way, not a payroll or a one-off fee) and the exact cost",
      hire_ok is False and train_ok is False and commission_ok is False
      and all(cause_of(message) == "cash_short" for message in (hire_message, train_message, commission_message))
      and all("50%" in message and "lender advances against a purchase" in message
              for message in (hire_message, train_message, commission_message))
      and "credit line" in hire_message and "{:,.0f}".format(round(hire_fee)) in hire_message,
      (hire_message, train_message, commission_message))

# spending_power('buy') counts the debt already carried: 500 into a 210 line can raise nothing.
set_position(-500.0, 210.0)
past_line_power = debtor.spending_power("buy")
past_line_ok, past_line_message = debtor.labour.commission("smith", 1.0)
set_position(400.0, 210.0)
solvent_power = debtor.spending_power("buy")
solvent_ok, solvent_message = debtor.labour.commission("smith", 9999.0)
set_position(-1000.0, 0.0)
check("scenario: commission() refuses a household already past its line and one over the half-line while solvent, so "
      "screen and command agree; auto_commission_for_blocked refuses outright when spending_power('buy') is exactly zero",
      abs(past_line_power) < 1e-9 and past_line_ok is False and abs(solvent_power - 505.0) < 1e-9 and solvent_ok is False
      and debtor.spending_power("buy") == 0.0 and debtor.labour.auto_commission_for_blocked() is None,
      (past_line_power, past_line_ok, solvent_power, solvent_ok))

# _waiting_on: the stalled-project pacing message reads spending_power('buy').
slow_pace_node = "academy_network"


def waiting_message(capital, credit_limit):
    set_position(capital, credit_limit)
    debtor.project_cost = lambda node_id: 9000.0
    debtor.active[slow_pace_node] = dict(ph_left=0.0, yrs=1.0, spent=0.0, cost_left=9000.0)
    try:
        return _WO(debtor, NODES, slow_pace_node, debtor.active[slow_pace_node], 9000.0)
    finally:
        debtor.active.pop(slow_pace_node, None)


roomy_waiting, indebted_waiting = waiting_message(50000.0, 2000.0), waiting_message(-50000.0, 2000.0)
check("scenario: a stalled project's waiting_on reads the pace as the blocker when there is real room, and tells a household "
      "50,000 past a 2,000 line that MONEY holds the project up",
      cause_of(roomy_waiting) == "money_pace" and cause_of(indebted_waiting) in ("money_blocked", "money_unfunded"),
      (roomy_waiting, indebted_waiting))

# The quote screen's figure is the number hire enforces.
set_position(-50000.0)
quoted = _protocol._spare_capacity(debtor, {})["you_could_raise_right_now"]
hire_in_debt_ok, hire_in_debt_message = debtor.labour.hire("smith", 1)
yearly_wage = S.ANNUAL_WAGE.get("smith", 375.0) * debtor.wage_index * debtor.price_index \
    * debtor.labour.market.price_factor("smith")
over_ok, over_message = debtor.labour.hire("smith", max(1, int(quoted // yearly_wage)) + 2)
debt_figure_matches = abs(quoted - debtor.spending_power("buy")) < 0.05
set_position(20000.0)
solvent_quote = _protocol._spare_capacity(debtor, {})["you_could_raise_right_now"]
solvent_hire_ok, solvent_hire_message = debtor.labour.hire("smith", 1)
reset_overrides(debtor)
check("scenario: the affordability figure the quote screen shows is the number hire enforces: matching spending_power('buy') "
      "in debt, a refusal when it is zero or the hire is past it, and a hire let through when the screen says thousands",
      debt_figure_matches and (quoted <= 0.0) == (hire_in_debt_ok is False) and over_ok is False
      and solvent_quote > 1000.0 and solvent_hire_ok is True,
      (quoted, debtor.spending_power("buy"), hire_in_debt_ok, over_ok, solvent_quote, solvent_hire_ok))

# --- scenario: every cash gate routes through spending_power, with the right kind.
# A rich household succeeds; the same household with the number forced to zero is refused, so the
# refusal is because of that number.
rich = sim(capital=1e9)
really_succeeds = (rich.labour.hire("smith", 1)[0] is True and rich.labour.train("machinist", 1, "smith")[0] is True
                   and rich.labour.commission("smith", 10.0)[0] is True)
gate_results = {}
for label, attempt in (("hire()", lambda: rich.labour.hire("smith", 1)),
                       ("train()", lambda: rich.labour.train("machinist", 1, "smith")),
                       ("commission()", lambda: rich.labour.commission("smith", 10.0))):
    calls = spending_power_spy(rich, forced=0.0)
    refused, refusal_message = attempt()
    reset_overrides(rich, "spending_power")
    gate_results[label] = (refused is False and bool(calls) and calls[0] == "buy")
calls = spending_power_spy(rich, forced=777.0)
refusal = rich.labour._cash_in_hand_refusal("a test fee", 1000.0)
reset_overrides(rich, "spending_power")
# presentation: the refusal prints the exact budget it was given
gate_results["_cash_in_hand_refusal"] = bool(calls) and calls[0] == "buy" and "777" in str(refusal)
calls = spending_power_spy(rich, forced=0.0)
commissioned = rich.labour.auto_commission_for_blocked()
reset_overrides(rich, "spending_power")
gate_results["auto_commission_for_blocked"] = commissioned is None and bool(calls) and calls[0] == "buy"
check("scenario: hire, train, commission, the cash-in-hand refusal and auto_commission_for_blocked each ask spending_power('buy') "
      "and follow its answer",
      really_succeeds and all(gate_results.values()), (really_succeeds, gate_results))

# open_venture and auto_open_ventures ask spending_power('open'), which does not count arrears.
rich.done.add(quick_payback)
rich._done_changed()
calls = spending_power_spy(rich, forced=0.0)
open_ok, open_message = rich.open_venture(quick_payback)
open_calls = list(calls)
calls = spending_power_spy(rich, forced=0.0)
opened_starved = rich.auto_open_ventures()
starved_calls = list(calls)
reset_overrides(rich, "spending_power")
check("scenario: open_venture() and auto_open_ventures() ask spending_power('open') and starving that answer keeps the concern "
      "shut, while the same concern opens on a rich household",
      open_ok is False and "open" in open_calls and quick_payback not in opened_starved and "open" in starved_calls
      and quick_payback in rich.auto_open_ventures(), (open_ok, open_calls, opened_starved, starved_calls))

# --- scenario: insolvency announces what a reputation penalty actually took
insolvent = sim(capital=-99999.0)
insolvent.reputation = 4.9
insolvent.insolvent_years = 30
insolvent.default_on_debt(150)
first_hit = [facts_of(message)["reputation_hit"] for _, message in insolvent.log if cause_of(message) == "insolvency_settled"][-1]
insolvent.capital = -99999.0
insolvent.insolvent_years = 30
insolvent.default_on_debt(200)
second_hit = [facts_of(message)["reputation_hit"] for _, message in insolvent.log if cause_of(message) == "insolvency_settled"][-1]
check("scenario: an insolvency announces the reputation it actually took, then that there was nothing left to take",
      first_hit == 4.9 and second_hit == 0.0, (first_hit, second_hit))

# --- scenario: a household deep in arrears does not commit to new work
bleeding = sim(manual=False)
bleeding.capital = -0.95 * bleeding.credit_limit()   # deep in arrears: near the limit before the year's interest
bleeding.insolvent_years = 20
bleeding.revenue = lambda: 0.0   # deep in arrears with no income: the needs bill alone leaves nothing to fund new work
bleeding.revenue_capacity = lambda: 0.0
active_before = len(bleeding.active)
bleeding.step()
check("scenario: a household deep in arrears with no income does not commit to new work",
      len(bleeding.active) <= active_before + 1, (len(bleeding.active), active_before))

# --- scenario: clearing the debt by working does not make you insolvent
worker = sim()
worker.end_year = worker.cfg["start_year"] + worker.cfg["horizon_years"]
replies = [S._agent_dispatch(worker, NODES, command) for command in (
    {"cmd": "start", "id": "arithmetic_positional"}, {"cmd": "step", "years": 1},
    {"cmd": "work", "trade": "scholar", "hours": 2000}, {"cmd": "step", "years": 1}, {"cmd": "state"})]
check("scenario: clearing your debt by working does not make you insolvent, and does not take your whole reputation with it",
      not any(cause_of(message) == "insolvency_settled" for _, message in worker.log)
      and not any(event.get("event_kind") == "insolvency_settled"
                  for reply in replies for event in (reply.get("events") or []))
      and replies[-1].get("reputation", 0) > 1.0,
      ([event for reply in replies for event in (reply.get("events") or []) if "INSOLVENCY" in str(event)],
       replies[-1].get("reputation")))

# --- scenario: a project part-paid when credit is withdrawn keeps what was paid
_pristine = pristine_game()
# the dearest project whose calendar floor outlasts a step and that 30% of its bill, in cash, can start
stopped = sim()
stopped.market_credit_room = lambda actor_id: None    # the household's own standing sets the line; the opening's loan book is fully lent to others
_candidates = sorted(((_pristine.project_cost(node_id), node_id) for node_id in NODES
                      if NODES[node_id]["yrs"] >= 2.0 and _pristine.start_reason(node_id)[0]), reverse=True)
for _cost, PACED in _candidates:
    stopped.capital = round(0.3 * _cost)
    if stopped.start_project(PACED)[0]:     # a refusal changes nothing
        break
stopped.step()      # one step: a calendar floor of two years leaves the project active only after the first
spent = stopped.active[PACED]["spent"]
part_paid = spent > 0 and stopped.active[PACED]["cost_left"] > 0
stopped.credit_limit = lambda: 0.0
stopped.capital = min(stopped.capital, -1.0)     # the household owes something when the credit is withdrawn
stopped.enforce_credit_limit(stopped.year)
kept_what_was_paid = abs(stopped.paid_towards.get(PACED, 0.0) - spent) < 0.5
event_names_it = any(PACED in message and "stands to your credit" in message for _, message in stopped.log)
stopped.capital, stopped.credit_frozen_until = 50000.0, 0
stopped.start_project(PACED)
# presentation: the event says what stands to your credit
check("scenario: a project part-paid when creditors stop the work keeps what was paid, the event says so and names the "
      "project, beginning again takes it off the bill, and the credit is spent once",
      part_paid and kept_what_was_paid and event_names_it
      and abs(stopped.active[PACED]["cost_left"] - (stopped.project_cost(PACED) - spent)) < 0.5
      and PACED not in stopped.paid_towards,
      (spent, stopped.paid_towards, stopped.active[PACED]["cost_left"], stopped.project_cost(PACED)))
