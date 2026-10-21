"""What to tell a household that has no room for more people: plain functions of the facts, no game."""
import math

from sim.refusal import Refusal

REOPENS_NAMED = 2
BUILDS_NAMED = 3


def sources_to_reopen(room_sources, done, operating, known, is_venture):
    """Room sources already built but shut, biggest first: reopening one is cheaper than building another."""
    shut = [(node_id, places) for node_id, places in room_sources
            if node_id in done and node_id in known and node_id not in operating and is_venture(node_id)]
    return sorted(shut, key=lambda source: -source[1])


def sources_to_build(room_sources, done, known, visible, distance):
    """Room sources not yet built, nearest in the tree first (then biggest)."""
    wanted = [(node_id, places) for node_id, places in room_sources
              if node_id not in done and node_id in known and visible(node_id)]
    return sorted(wanted, key=lambda source: (distance(source[0]), -source[1]))


def room_advice(housing_price_text, reopen, want, any_startable_now, places_text):
    """The advice for a household at its ceiling on people: housing first, then reopening, then building.

    `reopen` and `want` are [(node id, places)] as `sources_to_reopen` and `sources_to_build` give them."""
    reopen_bit = (
        ("you already have %s, shut: reopening %s is cheaper than building anything else. "
         % (" and ".join("%s (+%s)" % (node_id, places_text(places)) for node_id, places in reopen[:REOPENS_NAMED]),
            "it" if len(reopen) == 1 else "them"))
        if reopen else "")
    housing_bit = "Housing is bought: 'buy housing N' adds N places at %s each. " % housing_price_text
    housing = [{"action": "buy_housing", "node": None}]
    reopens = [{"action": "reopen", "node": node_id} for node_id, _places in reopen[:REOPENS_NAMED]]
    if not want:
        if reopen:
            return Refusal("room_advice", "%sThe rest is built - or in this case, "
                           "reopened: %s'open %s'." % (housing_bit, reopen_bit, reopen[0][0]),
                           remedies=housing + reopens)
        return Refusal("room_advice", "%sBeyond that, room comes from institutions and heavy "
                       "industry, and you have every one of them this society "
                       "offers; what is left grows on its own as they run." % housing_bit, remedies=housing)
    return Refusal("room_advice", "%sMore room is built: %s%s at your present income (the places grow "
                   "with surplus, since each needs people you can pay). Each is somewhere for "
                   "people to work and somebody to oversee them.%s"
                   % (housing_bit, reopen_bit,
                      "; ".join("%s (+%s places)" % (node_id, places_text(places)) for node_id, places in want[:BUILDS_NAMED]),
                      "" if any_startable_now else " None is startable today; they are listed "
                                                   "nearest first, so the first is what to work "
                                                   "towards."),
                   remedies=housing + reopens + [{"action": "build", "node": node_id} for node_id, _places in want[:BUILDS_NAMED]])


def hire_room_refusal(room, count, advice):
    """The refusal of a hire that would take the household past its room: the room is truncated, never rounded up."""
    room = max(0.0, room)
    whole = int(room)
    return Refusal("household_room", "you can supervise, house and teach %.2f more people, "
                   "not %g%s. %s"
                   % (math.floor(room * 100) / 100.0, count,
                      " - %d is the most whole people you can take" % whole
                      if whole else " - you have no room for even one",
                      advice), room=room, remedies=advice.facts["remedies"])
