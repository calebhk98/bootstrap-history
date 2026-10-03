"""`quote` for the commands that spend without being a `buy` target: hire,
commission, open, train and bounty.

Each quoter calls the same sim function the command charges with, so the
figure shown is the figure paid; nothing here does its own arithmetic for
an amount.
"""

from .util import _qty
from sim.engine import purchase_rule


def bounty_refusal(sim, nodes, node_id):
    """Why a bounty on this node cannot be posted, or None. `bounty` and
    `quote bounty` both ask this."""
    if node_id not in nodes:
        return "unknown node id %r" % node_id
    if node_id in sim.done:
        return "%s is already done" % node_id
    # Eligibility comes before the active-project rule: an active project's
    # prerequisites are already met, so this depends only on craft recognition.
    if not sim.bounty_eligible(node_id):
        node = nodes[node_id]
        missing = [prereq_id for prereq_id in node["pre"] if prereq_id not in sim.done]
        if missing:
            # The same fog filter `why` uses, so a prerequisite never leaks as a spoiler.
            return sim.missing_prereq_message(missing)
        return ("not bounty-eligible (category %s): a craftsman in %s could not "
                "recognise success at this without understanding the theory, so "
                "there is nothing to award the prize for. A bounty works where "
                "the craft already exists here and success is visible."
                % (node["cat"], sim.civ.get("name", "this society")))
    if node_id in sim.active:
        return ("%s is already active; stop it first if you want to switch to a "
                "bounty instead" % node_id)
    return None


def _quote_bounty(sim, nodes, cmd):
    node_id = cmd.get("id") or cmd.get("material")
    refusal = bounty_refusal(sim, nodes, node_id)
    if node_id not in nodes:
        return {"ok": False, "error": refusal}
    price = sim.bounty_price(node_id)
    reply = {"ok": True, "what": "bounty", "id": node_id,
             "eligible": refusal is None,
             "paid_now": round(price, 1),
             "price_multiplier": sim.BOUNTY_PRICE_MULTIPLIER,
             "ordinary_build_cost": round(sim.project_cost_now(node_id), 1),
             "you_have": round(sim.capital, 1),
             "you_could_raise": round(purchase_rule.purchase_budget(sim), 1),
             "afford_means": purchase_rule.afford_means(),
             "can_afford": purchase_rule.can_pay(sim, price),
             "when_it_pays_out": "the whole prize is paid when you post it; the "
                                 "work then runs on the project's own calendar "
                                 "with none of your hours or hired trades",
             "what_a_failure_costs": "a posted bounty is not refunded if the "
                                     "project is later stopped",
             "category_rule": "a bounty needs the craft to exist here so that "
                              "success is recognisable without theory"}
    if refusal:
        reply["refusal"] = refusal
    return reply


def _quote_hire(sim, nodes, cmd):
    trade = str(cmd.get("trade") or cmd.get("material") or "").strip().lower()
    count, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err}
    count, fee, refusal = sim.labour.hire_check(trade, count)
    if refusal:
        return {"ok": False, "error": refusal}
    per_year = sim.labour_market.quote_annual(trade, count) * count
    return {"ok": True, "what": "hire", "trade": trade, "people": count,
            "paid_now": round(fee, 1),
            "from_next_year_per_year": round(per_year, 1),
            "you_have": round(sim.capital, 1),
            "note": "Hiring pays a finder's fee that is also the first year's "
                    "wage, now; the same wage is due every year after."}


def _quote_commission(sim, nodes, cmd):
    trade = str(cmd.get("trade") or cmd.get("material") or "").strip().lower()
    hours, err = _qty(cmd, "hours") if "hours" in cmd else _qty(cmd, "n")
    if err:
        return {"ok": False, "error": err}
    fee, refusal = sim.labour.commission_check(trade, hours)
    if refusal:
        return {"ok": False, "error": refusal}
    return {"ok": True, "what": "commission", "trade": trade, "hours": hours,
            "paid_now": round(fee, 1), "you_have": round(sim.capital, 1),
            "note": COMMISSION_NOTE}


def _quote_train(sim, nodes, cmd):
    trade = str(cmd.get("trade") or cmd.get("material") or "").strip().lower()
    count, err = _qty(cmd, "n", 1)
    if err:
        return {"ok": False, "error": err}
    plan, refusal = sim.labour.train_check(trade, count, cmd.get("from"))
    if refusal:
        return {"ok": False, "error": refusal}
    return {"ok": True, "what": "train", "trade": trade, "people": plan["count"],
            "paid_now": round(plan["fee"], 1),
            "your_hours": round(plan["hours"], 1),
            "wage_bill_added_per_year": round(
                sim.labour.trainee_wage_bill(trade, plan["count"]), 1),
            "you_have": round(sim.capital, 1),
            "note": "Teaching pays their keep now and takes your own hours. "
                    "When they finish they join the payroll automatically and "
                    "the wage bill rises by the figure above every year."}


COMMISSION_NOTE = ("Commissioned hours are available to your projects this "
                   "year only, and cannot supervise a concern.")


def _quote_open(sim, nodes, cmd):
    node_id = cmd.get("id") or cmd.get("material")
    if node_id not in nodes:
        return {"ok": False, "error": "unknown node id %r" % (node_id,)}
    if node_id not in sim.done:
        return {"ok": False, "error": "you have not worked out how to do that yet, "
                                      "so there is nothing to open"}
    if not sim.is_venture(node_id):
        return {"ok": False, "error": "that is knowledge, not a going concern: "
                                      "there is nothing to open"}
    if node_id in sim.operating:
        return {"ok": False, "error": "you are already running that"}
    fee, units = sim.opening_fee(node_id, cmd.get("units"))
    reply = {"ok": True, "what": "open", "id": node_id, "paid_now": round(fee, 1),
             "size": units,
             "earns_a_year_when_ramped": round(
                 sim.venture_real_earnings(node_id, units, fully_ramped=True), 1),
             "costs_a_year_to_run": round(sim.venture_real_upkeep(node_id, units), 1),
             "you_have": round(sim.capital, 1),
             "can_afford": fee <= sim.spending_power("open")}
    shortfall = sim.opening_shortfall(node_id)
    if shortfall:
        reply["staff_short"] = ("needs %.1f scholars and %.1f craftsmen to "
                                "supervise; %.1f and %.1f are free" % shortfall)
    return reply


SPENDING_QUOTERS = {
    "hire": _quote_hire,
    "commission": _quote_commission,
    "train": _quote_train,
    "open": _quote_open,
    "bounty": _quote_bounty,
}
