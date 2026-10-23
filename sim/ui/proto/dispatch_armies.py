"""The army and armies commands: a country seat raises armies from its state's soldiers, sends them to a tile, recalls
them and stands them down (Complaint 485).

The rules are in `sim/world/campaign_*.py`, `battle.py` and `sim/agents/army_raising.py`, the records and orders in
`sim/engine/campaign_actors.py`; this module finds the seat's own country, hands the request over and shapes the
reply. A seat commands only its own country's armies. An army that ends its march on another actor's tile besieges
and storms it in the year's campaign phase; there is no declaration of war."""
from sim.refusal import Refusal

from .command_registry import command
from .dispatch_levers import seat_government


def _summary(army):
    return {"army": army.army_id, "owner": army.owner, "tile": army.tile, "soldiers": round(army.soldiers),
            "target": army.target, "food_kg": round(army.food_kg), "supply_state": round(army.supply_state, 3),
            "equipment_kg_per_soldier": round(army.equipment_kg, 2), "home_tile": army.home_tile,
            "pay_owed": round(army.pay_owed, 2), "events": list(army.log)}


def _reply(result, owner):
    if isinstance(result, Refusal):
        return {"ok": False, "cause": result.cause, "choices": result.choices, "error": str(result), **result.facts}
    return dict(_summary(result), ok=True, country=owner,
                note="armies march and fight in the year's campaign phase when you step.")


def army_reply(sim, cmd):
    government, owner, refusal = seat_government(sim, cmd)
    if refusal:
        return refusal
    words = str(cmd.get("text") or "").split()
    action = cmd.get("action") or (words[0] if words else None)
    rest = words[1:] if words and not cmd.get("action") else words
    if action == "raise":
        soldiers = cmd.get("soldiers", rest[0] if rest else None)
        try:
            soldiers = float(soldiers)
        except (TypeError, ValueError):
            pass
        return _reply(sim.raise_army(owner, soldiers, cmd.get("tile", rest[1] if len(rest) > 1 else None)), owner)
    if action in ("march", "recall", "disband"):
        army_id = cmd.get("army", rest[0] if rest else None)
        if action == "march":
            return _reply(sim.order_army(owner, army_id, cmd.get("tile", rest[1] if len(rest) > 1 else None)), owner)
        return _reply(sim.recall_army(owner, army_id) if action == "recall" else sim.disband_army(owner, army_id), owner)
    return {"ok": False, "cause": "unknown_action", "choices": ["raise", "march", "recall", "disband"],
            "error": "the army actions are raise, march, recall and disband. Nothing was changed."}


@command("army", shape="text", group="society",
         summary="raise, march, recall or disband one of your country's armies",
         usage=["army raise <soldiers> [tile]", "army march <army> <tile>", "army recall <army>", "army disband <army>",
                '{"cmd":"army","action":"raise","soldiers":5000,"tile":"italy_03"}'],
         options={"action": "raise, march, recall or disband", "soldiers": "soldiers to raise, out of those your state keeps "
                  "that are not already in an army", "army": "the army's id (see armies)",
                  "tile": "raise: the tile of yours to raise it on (your best-endowed one when none); march: the tile to go to"},
         description="An army is a slice of the soldiers your state keeps (the army line). It marches along the route "
                     "graph, eats what it carries, what its pack animals bring from your tiles in reach and what the tiles "
                     "it crosses give, and loses men to hunger, disease and desertion when its pay is owed. One that ends "
                     "up on another actor's tile besieges and storms it; a tile it wins passes to you. Refusals carry a "
                     "cause: household_seat_has_no_government, army_size_not_positive, not_enough_soldiers, tile_not_yours, "
                     "unknown_tile, unknown_army, not_your_army, unknown_action.")
def _cmd_army(sim, nodes, cmd, ended):
    return army_reply(sim, cmd)


@command("armies", shape="bare", group="society",
         summary="your country's armies: where they are, how many, how fed",
         usage=["armies", '{"cmd":"armies"}'],
         description="Lists the armies your country seat holds with their tile, numbers, order, food and supply state, "
                     "and the soldiers your state keeps that are in none.")
def _cmd_armies(sim, nodes, cmd, ended):
    government, owner, refusal = seat_government(sim, cmd)
    if refusal:
        return refusal
    return {"ok": True, "country": owner, "armies": [_summary(army) for army in sim.armies_of(owner)],
            "free_soldiers": round(sim.free_soldiers(owner))}
