"""The pay command: hand the state a sum once, to clear its debt or to fund what it owes interest groups."""

from .command_registry import command
from .quantity_units import read_quantity

TARGETS = ("debt", "claims")


@command("pay", group="money",
         summary="pay the state a sum once: its debt, what it owes interest groups, or a stated sum",
         usage=["pay state debt", "pay state claims", "pay state <amount>"],
         options={"debt": "all the state owes, or what your money covers of it",
                  "claims": "what the state has undertaken to make good to organised interest groups",
                  "<amount>": "money; anything past the debt is left in the state's purse as a reserve"},
         description="A one-off transfer from your purse to the state's. A smaller debt costs the state "
                     "less interest, and a state that can fund a group's claim does not raise it from "
                     "taxpayers. Works that do the same when finished are declared with the node mechanic "
                     "`transfer`.")
def _cmd_pay(sim, nodes, cmd, ended):
    if ended:
        return {"ok": False, "error": "the run has ended (%s); nothing more can be paid" % ended}
    target = str(cmd.get("what") or "").lower()
    if target in TARGETS:
        paid, text = sim.settle_with_state(target)
    else:
        amount, error = read_quantity(cmd, "amount", None, "money", "civ_coin", sim)
        if error:
            return {"ok": False, "error": error + ". Nothing was changed."}
        if not amount or amount <= 0:
            return {"ok": False, "error": "name `debt`, `claims` or a sum greater than zero. Nothing was changed."}
        paid, text = sim.settle_with_state(None, amount)
    if paid <= 0.0:
        return {"ok": False, "error": text + ". Nothing was changed."}
    return {"ok": True, "paid": round(paid, 1), "message": text, "capital": round(sim.capital, 1),
            "state_debt": round(sim.state_debt(), 1)}
