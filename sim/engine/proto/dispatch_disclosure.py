"""The disclose command: what to do with an invention you made (keep it secret, license it, publish it)."""

from .command_registry import command


def _number(cmd, key):
    value = cmd.get(key, 0.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


@command("disclose", group="society",
         summary="keep an invention secret, license it to a firm or the state, or publish it",
         usage=["disclose", "disclose <id> secret", "disclose <id> publish",
                "disclose <id> license <firm or state id> [fee N] [royalty R]",
                '{"cmd":"disclose","id":"<id>","mode":"license","licensee":"<actor id>","fee":1000,"royalty":0.05}'],
         options={"<id>": "an invention you have made",
                  "secret": "outsiders copy it only as fast as its trades and materials allow",
                  "license": "a named firm or the state pays the fee, can make it at once, and pays "
                             "the royalty (a share of its takings, firms only) every year",
                  "publish": "anyone may copy it and you gain standing; it cannot be taken back",
                  "(no choice)": "the default: it spreads as it always did, by being seen in use"},
         description="Bare disclose lists your inventions and what you chose for each, and who "
                     "can be licensed. Licence money moves between real purses.")
def _cmd_disclose(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    if node_id is None:
        return {"ok": True, "inventions": sim.disclosure_listing(),
                "can_license_to": sim.licensable_actor_ids()}
    fee, royalty = _number(cmd, "fee"), _number(cmd, "royalty")
    if fee is None or royalty is None:
        return {"ok": False, "error": "fee and royalty must be numbers"}
    reply = sim.disclose(node_id, str(cmd.get("mode", "")).strip().lower(),
                         licensee=cmd.get("licensee"), fee=fee, royalty=royalty)
    if reply["ok"]:
        reply["inventions"] = sim.disclosure_listing()
    return reply
