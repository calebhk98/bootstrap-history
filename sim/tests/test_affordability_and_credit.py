"""spending_power("buy" vs "start"/"open"), credit_limit, arrears,
insolvency and the warnings and refusals built on them.

A few games are built once and reused; checks that only read a figure reset the instance
overrides they installed (credit_limit, spending_power, project_cost) before the next check.
"""
from .harness import *  # noqa: F401,F403


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


# --- auto_open: says why it refuses, and in deep arrears opens only what pays for its own door.
opener = sim(capital=1.0)
best_concern = max((node_id for node_id in NODES if NODES[node_id]["rev"] > NODES[node_id]["up"] > 0),
                   key=lambda node_id: NODES[node_id]["rev"] - NODES[node_id]["up"])
opener.done.add(best_concern)
opener._done_changed()
opened = opener.auto_open_ventures()
check("auto_open opens nothing it cannot pay the capex on", best_concern not in opened, (best_concern, opened[:3]))
check("auto_open says why the best concern is still shut",
      any(best_concern in message for _, message in opener.log), [message for _, message in opener.log][:2])

# A completed, earning concern that pays for its door within months opens even deep in arrears;
# a slow one and an institution do not.
quick_payback, slow_payback = "hom_button", "fin_stamp"
for node_id in (quick_payback, slow_payback):
    assert NODES[node_id]["rev"] > NODES[node_id]["up"], node_id
deep = sim(capital=-50000.0)
deep.done.add(quick_payback)
deep._done_changed()
check("the household in this check really is deep in arrears (over half its credit line)",
      deep.capital < 0 and -deep.capital > deep.credit_limit() * 0.5, (deep.capital, deep.credit_limit()))
check("a completed concern that pays for its own door within months opens even while deep in arrears",
      quick_payback in deep.auto_open_ventures(), quick_payback)
deep.capital = -50000.0
deep.done.add(slow_payback)
deep._done_changed()
deep.log.clear()
opened_slow = deep.auto_open_ventures()
check("a completed concern that would take years to pay for its own door stays shut while deep in arrears",
      slow_payback not in opened_slow, (slow_payback, opened_slow))
check("...and the refusal names its own payback period and what would clear it",
      any("pay for its own doors" in message and "clear enough debt" in message for _, message in deep.log),
      [message for _, message in deep.log])
deep.done.add("workshop_first")
deep._done_changed()
check("an institution still opens nothing while deep in arrears",
      "workshop_first" not in deep.auto_open_ventures(), "workshop_first")

# --- one affordability rule, the quote screen and hint use it.
fresh = sim()
check("a household that is not near its credit limit is not warned",
      (fresh.warn_near_the_limit(105), not fresh.log)[1], [message for _, message in fresh.log])
fresh_start_power = fresh.spending_power("start")
available_reply = S._agent_dispatch(fresh, NODES, {"cmd": "available"})
hint = str((available_reply.get("to_see_more") or {}).get("what you can pay for", ""))
check("the AFFORD hint uses the rule `start` uses, since it is about starting",
      str(int(fresh_start_power)).replace(",", "") in hint.replace(",", ""), hint)
money_reply = S._agent_dispatch(fresh, NODES, {"cmd": "money"})
check("the ledger says how much of the credit line is used",
      money_reply.get("of_that_limit_you_have_used") is not None, money_reply.get("of_that_limit_you_have_used"))
check("a founder with a practice can still just reach a cover identity",
      fresh.capital + fresh.credit_limit() >= fresh.project_cost("identity_cover"),
      (fresh.capital + fresh.credit_limit(), fresh.project_cost("identity_cover")))
thin_credit_limit = fresh.credit_limit()
thin_living_cost = fresh.living_cost()
starting_capital = fresh.capital

# The credit limit warns before it is crossed, once, and not once it is past.
fresh.capital = -fresh.credit_limit() * 0.75
fresh.warn_near_the_limit(105)
check("the credit limit warns you BEFORE you cross it",
      any("CLOSE TO THE LIMIT" in message for _, message in fresh.log), [message for _, message in fresh.log])
check("...and names what you could still do about it",
      any("stop" in message and "mothball" in message for _, message in fresh.log), [message for _, message in fresh.log][:1])
log_length = len(fresh.log)
fresh.warn_near_the_limit(106)
check("...and does not say it again every year", len(fresh.log) == log_length, len(fresh.log) - log_length)
fresh.capital = -fresh.credit_limit() * 1.03
fresh.log.clear()
fresh.warn_near_the_limit(107)
check("the limit warning is about what is ahead of you, not behind",
      not fresh.log, [message for _, message in fresh.log])
fresh.capital = starting_capital

# A lender does not cut your line because you took a job this year.
full_credit_limit = fresh.credit_limit()
fresh.wage_hours_this_year = fresh.labour.director_pool()
check("a lender does not cut your line because you took a job this year",
      abs(fresh.credit_limit() - full_credit_limit) < 1e-6, (full_credit_limit, fresh.credit_limit()))
fresh.wage_hours_this_year = 0.0

# A grand friend does not lend more than income can carry.
fresh.done.add("patron_senatorial")
fresh._done_changed()
check("a grand friend does not lend you more than your income can carry",
      fresh.credit_limit() < thin_credit_limit * 3, (thin_credit_limit, fresh.credit_limit()))
check("...and the interest on the whole line stays under what you earn",
      fresh.credit_limit() * fresh.debt_interest_rate() < fresh.revenue(),
      (fresh.credit_limit() * fresh.debt_interest_rate(), fresh.revenue()))

# Status upkeep is conditional on being able to afford it.
fresh.done.add("citizenship")
fresh._done_changed()
ruined_living_cost = fresh.living_cost()
check("a ruined household stops keeping up appearances",
      ruined_living_cost < thin_living_cost + 50.0, (ruined_living_cost, thin_living_cost))
fresh.capital = 2000000.0
check("...and a household that can afford the show still pays for it",
      fresh.living_cost() > ruined_living_cost * 2, (fresh.living_cost(), ruined_living_cost))

# --- the arrears banner quotes what the ledger does, and its wage-work advice gains.
arrears = sim(capital=-4000.0)
arrears.insolvent_years = 20
arrears.revenue = lambda: 0.0
diagnosis = arrears.stall_diagnosis()
ledger_loss = (arrears.revenue() - arrears.upkeep() - arrears.living_cost() - arrears.mine_operating_cost()
               - max(0.0, -arrears.capital) * arrears.debt_interest_rate())
check("the arrears banner quotes the same loss the ledger does",
      diagnosis and "{:,.0f}".format(-ledger_loss) in diagnosis["you_are_stuck"], (diagnosis or {}).get("you_are_stuck"))
check("...and names the part of it that is interest on the arrears themselves",
      any("interest on the arrears" in reason for reason in diagnosis["what_would_change_it"]),
      diagnosis["what_would_change_it"])
wage_game = sim(civ="norse_900ad", capital=-4000.0)  # a civilisation whose own practice pays less than wage work
wage_game.insolvent_years = 20
wage_advice = [reason for reason in (wage_game.stall_diagnosis() or {}).get("what_would_change_it", [])
               if reason.startswith("work as a ")]
# The advice's quote is what work_for_wages pays for the trade and hours it names.
quote_match = re.match(r"work as a (\w+): (\d+) of your own hours .* bring in about ([\d,]+) against the ([\d,]+) of practice",
                       wage_advice[0]) if wage_advice else None
check("a stalled household in debt is offered wage work, with trade, hours and earning",
      quote_match, wage_advice)
if quote_match:
    quoted_trade, quoted_hours = quote_match.group(1), int(quote_match.group(2))
    quoted_earning, quoted_practice = (int(quote_match.group(index).replace(",", "")) for index in (3, 4))
    _, _, practice_given_up = wage_game.labour.work_for_wages_dry_run(quoted_trade, quoted_hours)
    check("the practice the banner says is given up is what the sale costs",
          abs(practice_given_up - quoted_practice) <= 1, (quoted_practice, practice_given_up))
    capital_before = wage_game.capital
    paid, refusal = wage_game.labour.work_for_wages(quoted_trade, quoted_hours)
    check("the advised work is accepted", refusal is None, refusal)
    check("the money moved is the earning the banner quoted",
          abs(paid - quoted_earning) <= 1 and abs((wage_game.capital - capital_before) - paid) < 1e-6,
          (quoted_earning, paid, wage_game.capital - capital_before))
    check("the banner names the trade that pays most an hour",
          quoted_trade == wage_game.labour.best_wage_trade(), (quoted_trade, wage_game.labour.best_wage_trade()))

# --- an idle fortune bleeds living costs, and the ledger names the part that is wealth.
rich_ledger = S._agent_dispatch(sim(capital=hours_money(20200000)), NODES, {"cmd": "money"})
check("the ledger names the part of your living costs that is your wealth",
      (rich_ledger.get("what_it_costs_you") or {}).get("_of_which_because_you_are_rich", 0) > 1000,
      rich_ledger.get("what_it_costs_you"))

# --- refusals and quotes in debt, on one game whose capital and credit line are set per case.
debtor = sim(capital=0.0)


def set_position(capital, credit_limit=None):
    reset_overrides(debtor)
    debtor.capital = capital
    if credit_limit is not None:
        debtor.credit_limit = lambda: credit_limit


debtor.capital = 400.0
check("there is ONE affordability rule, and it says which it is using",
      abs(debtor.spending_power("buy") - (400.0 + debtor.credit_limit() * 0.5)) < 1e-6
      and abs(debtor.spending_power("start") - (400.0 + debtor.credit_limit())) < 1e-6,
      (debtor.spending_power("buy"), debtor.spending_power("start")))
quote_reply = S._agent_dispatch(debtor, NODES, {"cmd": "quote", "what": "mine", "material": "coal", "n": 500})
check("quote counts the credit a lender would actually advance",
      quote_reply.get("you_could_raise", 0) > quote_reply.get("you_have", 0), quote_reply.get("you_could_raise"))

# hire/train/commission may draw only half the credit line; the refusal says which rule and why.
set_position(-50000.0)
hire_ok, hire_message = debtor.labour.hire("smith", 3)
check("a cash-short hire is still refused (the asymmetry itself is kept)", hire_ok is False, (hire_ok, hire_message))
check("...but the refusal says WHICH rule this is: half the credit line, not all of it",
      "50%" in hire_message and "credit line" in hire_message, hire_message)
check("...and WHY: a lender funds work under way, not a payroll or a one-off fee",
      "lender advances against a purchase" in hire_message, hire_message)
hire_fee = debtor.labour.hire_fee("smith", 3)
check("...and states the exact cost hire() computed",
      "{:,.0f}".format(round(hire_fee)) in hire_message, (hire_fee, hire_message))
train_ok, train_message = debtor.labour.train("machinist", 3, None)
check("train's cash-short refusal uses the identical reasoning as hire's",
      train_ok is False and "50%" in train_message and "lender advances against a purchase" in train_message,
      train_message)
commission_ok, commission_message = debtor.labour.commission("smith", 3500.0)
check("commission's cash-short refusal uses the same reasoning too",
      commission_ok is False and "50%" in commission_message
      and "lender advances against a purchase" in commission_message, commission_message)

# spending_power('buy') counts the debt already carried: 500 into a 210 line can raise nothing.
set_position(-500.0, 210.0)
check("spending_power('buy') counts the debt already carried: 500 into a 210 line can raise nothing",
      abs(debtor.spending_power("buy")) < 1e-9, debtor.spending_power("buy"))
past_line_ok, past_line_message = debtor.labour.commission("smith", 1.0)
check("...and commission() refuses a household already past its line, so screen and command agree",
      past_line_ok is False, (past_line_ok, past_line_message))
set_position(400.0, 210.0)
check("...and it is still capital plus half the line when there is no hole to count",
      abs(debtor.spending_power("buy") - 505.0) < 1e-9, debtor.spending_power("buy"))
solvent_ok, solvent_message = debtor.labour.commission("smith", 9999.0)
check("...and still refuses a fee over the half-line once the household is solvent again",
      solvent_ok is False, (solvent_ok, solvent_message))
set_position(-1000.0, 0.0)
check("auto_commission_for_blocked refuses outright when spending_power('buy') is exactly zero",
      debtor.spending_power("buy") == 0.0 and debtor.labour.auto_commission_for_blocked() is None,
      debtor.spending_power("buy"))

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


check("_waiting_on reads the pace as the blocker when there is real room",
      "pace" in waiting_message(50000.0, 2000.0), waiting_message(50000.0, 2000.0))
check("a household 50,000 past a 2,000 line is told MONEY is what holds the project up",
      "money" in waiting_message(-50000.0, 2000.0), waiting_message(-50000.0, 2000.0))

# The quote screen's figure is the number hire enforces.
set_position(-50000.0)
quoted = _protocol._spare_capacity(debtor, {})["you_could_raise_right_now"]
check("the affordability figure the quote screen shows while in debt matches spending_power('buy')",
      abs(quoted - debtor.spending_power("buy")) < 0.05, (quoted, debtor.spending_power("buy")))
hire_in_debt_ok, hire_in_debt_message = debtor.labour.hire("smith", 1)
check("...and when that figure is zero because the household is past its line, hire() refuses too",
      (quoted <= 0.0) == (hire_in_debt_ok is False), (quoted, hire_in_debt_ok, hire_in_debt_message))
yearly_wage = S.ANNUAL_WAGE.get("smith", 375.0) * debtor.wage_index * debtor.price_index \
    * debtor.labour.market.price_factor("smith")
over_ok, over_message = debtor.labour.hire("smith", max(1, int(quoted // yearly_wage)) + 2)
check("...and a hire past what the quote screen says the household could raise is refused",
      over_ok is False, (quoted, over_message))
set_position(20000.0)
solvent_quote = _protocol._spare_capacity(debtor, {})["you_could_raise_right_now"]
solvent_hire_ok, solvent_hire_message = debtor.labour.hire("smith", 1)
check("...and a solvent household the screen says can raise thousands is let through by hire()",
      solvent_quote > 1000.0 and solvent_hire_ok is True, (solvent_quote, solvent_hire_ok, solvent_hire_message))
reset_overrides(debtor)

# --- every cash gate routes through spending_power, with the right kind.
# A rich household succeeds; the same household with the number forced to zero is refused, so the
# refusal is because of that number.
rich = sim(capital=1e9)
check("hire() really does succeed on a rich household", rich.labour.hire("smith", 1)[0] is True, "hire")
check("train() really does succeed on a rich household", rich.labour.train("machinist", 1, "smith")[0] is True, "train")
check("commission() really does succeed on a rich household", rich.labour.commission("smith", 10.0)[0] is True, "commission")
for label, attempt in (("hire()", lambda: rich.labour.hire("smith", 1)),
                       ("train()", lambda: rich.labour.train("machinist", 1, "smith")),
                       ("commission()", lambda: rich.labour.commission("smith", 10.0))):
    calls = spending_power_spy(rich, forced=0.0)
    refused, refusal_message = attempt()
    reset_overrides(rich, "spending_power")
    check("%s asks spending_power('buy') and its refusal follows that answer" % label,
          refused is False and calls and calls[0] == "buy", (refused, calls, refusal_message))
calls = spending_power_spy(rich, forced=777.0)
refusal = rich.labour._cash_in_hand_refusal("a test fee", 1000.0)
reset_overrides(rich, "spending_power")
check("_cash_in_hand_refusal asks spending_power('buy') and prints the exact number it got back",
      calls and calls[0] == "buy" and "777" in refusal, (calls, refusal))
calls = spending_power_spy(rich, forced=0.0)
commissioned = rich.labour.auto_commission_for_blocked()
reset_overrides(rich, "spending_power")
check("auto_commission_for_blocked asks spending_power('buy') and a zero answer shuts it down",
      commissioned is None and calls and calls[0] == "buy", (commissioned, calls))

# open_venture and auto_open_ventures ask spending_power('open'), which does not count arrears.
rich.done.add(quick_payback)
rich._done_changed()
calls = spending_power_spy(rich, forced=0.0)
open_ok, open_message = rich.open_venture(quick_payback)
check("open_venture() asks spending_power('open') and its refusal follows that answer",
      open_ok is False and "open" in calls, (open_ok, calls, open_message))
calls = spending_power_spy(rich, forced=0.0)
opened_starved = rich.auto_open_ventures()
reset_overrides(rich, "spending_power")
check("auto_open_ventures() asks spending_power('open') and starving that answer keeps the concern shut",
      quick_payback not in opened_starved and "open" in calls, (opened_starved, calls))
check("auto_open_ventures() really does open the same concern on a rich household",
      quick_payback in rich.auto_open_ventures(), quick_payback)

# --- insolvency announces what a reputation penalty actually took.
insolvent = sim(capital=-99999.0)
insolvent.reputation = 4.9
insolvent.insolvent_years = 30
insolvent.enforce_credit_limit(150)
check("a reputation penalty announces what it actually took",
      "-4.9" in [message for _, message in insolvent.log if "INSOLVENCY" in message][-1], insolvent.log[-1:])
insolvent.capital = -99999.0
insolvent.insolvent_years = 30
insolvent.enforce_credit_limit(200)
check("...and says plainly when there was nothing left to take",
      "already at nothing" in [message for _, message in insolvent.log if "INSOLVENCY" in message][-1],
      insolvent.log[-1:])

# --- a household deep in arrears does not commit to new work.
bleeding = sim(capital=-74600.0 * sim().labour.money_per_labour_hour(), manual=False)
bleeding.insolvent_years = 20
active_before = len(bleeding.active)
bleeding.step()
check("a household deep in arrears does not commit to new work",
      len(bleeding.active) <= active_before + 1, (len(bleeding.active), active_before))

# --- clearing the debt by working does not make you insolvent.
worker = sim()
worker.end_year = worker.cfg["start_year"] + worker.cfg["horizon_years"]
replies = [S._agent_dispatch(worker, NODES, command) for command in (
    {"cmd": "start", "id": "arithmetic_positional"}, {"cmd": "step", "years": 1},
    {"cmd": "work", "trade": "scholar", "hours": 2000}, {"cmd": "step", "years": 1}, {"cmd": "state"})]
check("clearing your debt by working does not make you insolvent",
      not any("INSOLVENCY" in json.dumps(reply) for reply in replies),
      [event for reply in replies for event in (reply.get("events") or []) if "INSOLVENCY" in str(event)])
check("...and does not take your whole reputation with it",
      replies[-1].get("reputation", 0) > 1.0, replies[-1].get("reputation"))

# --- a project part-paid when credit is withdrawn keeps what was paid.
stopped = sim(capital=round(0.3 * sim().project_cost("identity_cover")))
stopped.start_project("identity_cover")
for _ in range(2):
    stopped.step()
spent = stopped.active["identity_cover"]["spent"]
check("a project part-paid for has really been part-paid for", spent > 100, spent)
stopped.credit_limit = lambda: 0.0
stopped.enforce_credit_limit(stopped.year)
check("the creditors stopping your work does not burn what you paid",
      abs(stopped.paid_towards.get("identity_cover", 0.0) - spent) < 0.5, stopped.paid_towards)
check("...and the event says so, and names what it stopped",
      any("identity_cover" in message and "stands to your credit" in message for _, message in stopped.log),
      [message for _, message in stopped.log if "CREDIT EXHAUSTED" in message][:1])
stopped.capital, stopped.credit_frozen_until = 50000.0, 0
stopped.start_project("identity_cover")
check("...and beginning again takes it off the bill",
      abs(stopped.active["identity_cover"]["cost_left"] - (stopped.project_cost("identity_cover") - spent)) < 0.5,
      (stopped.active["identity_cover"]["cost_left"], stopped.project_cost("identity_cover")))
check("...and the credit is spent once, not every time",
      "identity_cover" not in stopped.paid_towards, stopped.paid_towards)

# --- a household past its credit line keeps no door fee to spend: opening a shut concern waits.
past_line = sim(capital=-1.0)
past_line.done.add(quick_payback)
past_line._done_changed()
past_line.state.household.capital = -3.0 * past_line.credit_limit()
check("nothing can be opened with a door fee once the debt is past the credit line",
      past_line.spending_power("open") == 0.0 and quick_payback not in past_line.auto_open_ventures(),
      (past_line.spending_power("open"), past_line.capital, past_line.credit_limit()))
