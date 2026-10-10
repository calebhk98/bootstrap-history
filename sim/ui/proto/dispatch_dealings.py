"""The dealings commands: patents, offers and shares. A seat deals through the same exchange every actor uses."""

from .command_registry import command


def _share(cmd, key="share"):
    value = cmd.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 < float(value) <= 1.0:
        return None
    return float(value)


def _price(cmd):
    value = cmd.get("price", 0.0)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) < 0.0:
        return None
    return float(value)


@command("patent", group="society",
         summary="apply for the exclusive right to an invention you made, or list what you hold",
         usage=["patent", "patent <id>", '{"cmd":"patent","id":"<id>"}'],
         options={"<id>": "an invention you hold; a state that knows the patent institution grants the right for a term",
                  "(no id)": "list your patents, the shares you hold and issued, and the offers waiting for you"},
         description="A patent lets you sell the right or licence it through an offer. Others may still practise the "
                     "invention unlicensed: the state enforces the right only as far as its capacity reaches, and a "
                     "holder who catches an infringer is paid the margin the infringer made.")
def _cmd_patent(sim, nodes, cmd, ended):
    node_id = cmd.get("id")
    if node_id is None:
        return dict(sim.dealings_listing(), ok=True)
    return sim.seat_patent(node_id)


@command("offer", group="society",
         summary="offer another actor or player things for things: money, patents, licences, shares",
         usage=['{"cmd":"offer","to":"<actor id>","give":{"licence":["<id>"],"royalty":{"<id>":0.05}},"take":{"money":1000}}',
                '{"cmd":"offer","to":"<actor id>","give":{"patent":["<id>"]},"take":{"money":5000}}'],
         options={"to": "a firm, a state, a stratum or another seat",
                  "give": "what you hand over: money, patent [ids], licence [ids] with royalty {id: share of takings}, "
                          "shares {issuer id: share of its equity}",
                  "take": "what you ask for, in the same terms"},
         description="The offer waits two years in the receiver's offers. An AI actor answers at the next year's turn: "
                     "it takes an offer worth more to it than it costs. Another player answers with accept or decline.")
def _cmd_offer(sim, nodes, cmd, ended):
    return sim.seat_offer(cmd.get("to"), cmd.get("give"), cmd.get("take"))


@command("offers", shape="bare", group="society",
         summary="the offers made to you",
         usage=["offers", '{"cmd":"offers"}'], options={},
         description="Lists each offer made to your seat, with who made it and what it gives and asks.")
def _cmd_offers(sim, nodes, cmd, ended):
    return {"ok": True, "offers": sim.dealings_listing()["offers"]}


@command("accept", group="society",
         summary="accept an offer made to you",
         usage=["accept <offer id>", '{"cmd":"accept","offer":"<offer id>"}'],
         options={"<offer id>": "an id from offers"},
         description="Both sides are checked again and nothing moves unless everything still holds.")
def _cmd_accept(sim, nodes, cmd, ended):
    return sim.seat_answer(cmd.get("offer"), True)


@command("decline", group="society",
         summary="decline an offer made to you",
         usage=["decline <offer id>", '{"cmd":"decline","offer":"<offer id>"}'],
         options={"<offer id>": "an id from offers"},
         description="The offer is dropped and nothing moves.")
def _cmd_decline(sim, nodes, cmd, ended):
    return sim.seat_answer(cmd.get("offer"), False)


@command("shares", group="society",
         summary="issue shares in your own business, buy shares in another, or list what you hold",
         usage=["shares", '{"cmd":"shares","do":"issue","share":0.2,"to":"<actor id>","price":5000}',
                '{"cmd":"shares","do":"buy","issuer":"<actor id>","share":0.1,"from":"<holder id>","price":800}'],
         options={"issue": "sell a share of your own equity; its holders draw dividends from your margin",
                  "buy": "buy a share of another actor's equity from a holder, or from the issuer itself"},
         description="Both are offers (see offer), so the receiver answers as to any offer. Dividends are paid each year "
                     "by share from the issuer's margin.")
def _cmd_shares(sim, nodes, cmd, ended):
    what = cmd.get("do")
    if what is None:
        return dict(sim.dealings_listing(), ok=True)
    share, price = _share(cmd), _price(cmd)
    if share is None or price is None:
        return {"ok": False, "error": "share is a part of the equity above 0 and at most 1, and price is not negative"}
    if what == "issue":
        return sim.seat_offer(cmd.get("to"), {"shares": {sim.state.acting_seat: share}}, {"money": price})
    if what == "buy":
        issuer = cmd.get("issuer")
        if not isinstance(issuer, str) or not issuer:
            return {"ok": False, "error": "name the issuer whose shares you want"}
        return sim.seat_offer(cmd.get("from") or issuer, {"money": price}, {"shares": {issuer: share}})
    return {"ok": False, "error": "do is issue or buy"}
