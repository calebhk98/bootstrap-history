"""The found command: a seat that holds the deposit-banking institution puts capital into a bank of its own."""

from .command_registry import command
from sim.engine import ui_port


@command("found", group="money",
         summary="found a bank with your own capital, once you know how to take deposits",
         usage=["found bank <amount>", '{"cmd":"found","what":"bank","capital":2000}'],
         options={"bank": "a bank that takes households' deposits and lends them on", "<amount>": "money of yours to put into it"},
         description="Needs a technology that lets a society's households found banks (the deposit bank). Your capital is "
                     "the bank's own: it covers its first loans and its losses, depositors who see it thin or its record "
                     "poor withdraw, and a bank that cannot pay them sells its loans or fails, its depositors and you "
                     "bearing the loss. What it earns beyond its capital is paid to you.")
def _cmd_found(sim, nodes, cmd, ended):
    if cmd.get("what") != "bank":
        return {"ok": False, "error": "found what? 'found bank <amount>' founds a bank."}
    return sim.send(ui_port.FoundBank(cmd.get("capital")))
