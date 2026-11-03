"""What to tell a player who has hit a wall on people: what raises the ceiling and what buys more staff."""
from sim.refusal import Refusal

from .room_advice import room_advice, sources_to_build, sources_to_reopen
from .staff_advice import staff_remedies


class Advice:
    def __init__(self, world, capacity, hands):
        self._world = world
        self.capacity = capacity
        self.hands = hands

    # What each of these adds to the CEILING on people, taken from
    # staff_capacity below so the advice and the arithmetic cannot drift apart.
    # THESE ARE THE SAME NUMBERS AS STAFF_CAPACITY_SOURCES's own artisan (`ar`)
    # column below, for every node the two tables share, kept as INT here
    # (whole household places, for "%d" advice text) rather than the float
    # STAFF_CAPACITY_SOURCES needs for its own unit-scaled arithmetic - two
    # declared names per figure rather than one, so a rename or a cast can
    # never silently turn a place count into a fraction of one.
    # ROOM_SOURCES: [(node id, places)] from each node's `room_places`, as the mechanics module's view gives them.
    # fin_trial_balance, fin_company_town and fin_chain_store - the
    # organisation entries added alongside STAFF_CAPACITY_SOURCES above - are
    # deliberately NOT in ROOM_SOURCES, even though every one of them raises
    # the same ceiling every other entry here does. room_advice's own
    # "nearest first" sort (below) ranks by CLOSURE SIZE, a proxy that holds
    # for the furnace-and-patronage tree above because a shallow node there
    # is also a cheap one. It does not hold for the finance branch: the whole
    # point of fin_chain_store's own note ("requires sophisticated management
    # and accounting") is that it is a late, expensive, 30,000-denarii
    # institution sitting only two prerequisites deep (fin_market ->
    # fin_department_store), so ranking it by closure size alone told a
    # founder with four hundred denarii in year 100 that the NEAREST way to
    # more room was a chain of department stores - a measured, not a
    # theoretical, failure of this heuristic once a second branch of the
    # tree with a different shape is let into it. The institutions
    # themselves are real (STAFF_CAPACITY_SOURCES, supervision_room); this
    # one piece of advice text is not worth teaching the sort to weigh cost
    # as well as depth for three nodes, so they are simply left unnamed here
    # - a player who builds them (for their own revenue, or for the
    # household room staff_capacity() already credits them with) still gets
    # the room; this function just never tells them to go build one.

    def _places_text(self, places):
        """The places a node adds at the current income, as a short number."""
        added = self.capacity.room_added_by(places)
        return "%.1f" % added if added < 10 else "%d" % round(added)

    def room_advice(self):
        """What raises the CEILING on people, which is not what buys people.

        The household-room refusal must not hand back staff_advice, which
        names hiring, commissioning and buying - every one of which needs
        room you do not have. The room comes from institutions and heavy
        industry, and this has to point at those instead.
        """
        # A CLOSED ROOM SOURCE IS NOT A MISSING ONE: staff_capacity() already
        # drops a source's places the moment its venture is not running (see
        # STAFF_CAPACITY_SOURCES's must_be_running), so the advice below must
        # distinguish never-built (`k not in projects.done`) from
        # built-but-not-running - a school built, then shut for want of a
        # supervisor, must still be named as the cheapest way back, not
        # just dropped from the count. Filtering only on `done` would tell
        # a player who hit the ceiling it had been holding up to build
        # endowment_land or court an imperial patron, instead of simply
        # reopening what they already own.
        projects = self._world.projects
        reopen = sources_to_reopen(self._world.knowledge.ROOM_SOURCES, projects.done, projects.operating, self._world.scenario.nodes,
                                   self._world.knowledge.is_venture)
        # NEAREST FIRST, and nearest means how much of the tree stands between
        # you and it. Sorted on size alone this offered power_grid (+130) to a
        # founder with six places - the last node in the game, true and
        # useless - while workshop_first, one prerequisite away, went unnamed.
        want = sources_to_build(self._world.knowledge.ROOM_SOURCES, projects.done, self._world.scenario.nodes, self._world.knowledge.is_visible,
                                lambda node_id: len(self._world.scenario.closure(node_id) - projects.done))
        startable_now = any(self._world.knowledge.start_reason(node_id, _why=False)[0] for node_id, _places in want)
        return room_advice(self._world.money_text(self._world.finance.housing_price_per_place(), grouped=True),
                           reopen, want, startable_now, self._places_text)

    def staff_advice(self, kind, deficit=None):
        """Name the remedy, not just the shortfall - and only remedies you could
        actually have heard of.

        Advice that says "build workshop_first" while `why workshop_first`
        replies "you have never heard of that" from the same program in the
        same second is a contradiction, not help. Hiring is always
        sayable, because the labour market is in front of you; a named
        institution is not, until it is.

        `deficit` is how many more people the caller is short; the hire
        advice is sized to it.
        """
        projects = self._world.projects

        def waiting_on_kind(node_id):
            # Asked DIRECTLY of the node's own requirement, never through start_reason, which calls this function.
            node = self._world.scenario.nodes[node_id]
            return (node["art"] > self._world.workforce.artisans + 1e-9 if kind == "artisans"
                    else node["sch"] > self.hands.effective_scholars() + 1e-9)

        steps = staff_remedies(kind, self._world.knowledge.STAFF_SOURCES.get(kind, []), deficit, projects.done,
                               projects.operating, self._world.knowledge.is_venture, self._world.knowledge.is_visible, waiting_on_kind,
                               self._world.knowledge.staff_hire_advice)
        bits = [sentence for sentence, _remedy in steps]
        remedies = [remedy for _sentence, remedy in steps]
        if not bits:
            return Refusal("staff_advice", "wait: your existing institutions add %s each year." % kind, remedies=[])
        return Refusal("staff_advice", "To get more %s: %s." % (kind, "; ".join(bits[:3])), remedies=remedies[:3])
