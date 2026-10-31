"""Every seat is told the hazard notices from its own state: the "already told" memo is the seat's, and the year's summary
of what struck holds each seat's own lines."""
QUICK_TOPIC = True

import unittest
from contextlib import contextmanager

from sim.hazards.commands import SayOnce
from sim.hazards.state import HazardsSeat
from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness


def two_seats(**views):
    """A hazards module whose acting seat, seat state and event log follow `act_as`; also the logs by seat."""
    states = {"alpha": HazardsSeat(), "beta": HazardsSeat()}
    logs = {"alpha": [], "beta": []}
    acting = {"seat": "alpha"}
    holder = {}

    @contextmanager
    def act_as(seat_id):
        before, acting["seat"] = acting["seat"], seat_id
        holder["module"].seat = states[seat_id]
        try:
            yield
        finally:
            acting["seat"] = before
            holder["module"].seat = states[before]

    module = hazards_host.build(act_as=act_as, acting_seat=lambda: acting["seat"], seat=states["alpha"],
                                event_log=lambda: logs[acting["seat"]], **views)
    holder["module"] = module
    return module, logs


class SayOncePerSeat(unittest.TestCase):

    def test_a_notice_told_to_one_seat_is_still_new_to_the_other(self):
        module, _ = two_seats()
        told = []
        for seat_id in ("alpha", "beta", "alpha", "beta"):
            with module.needs.act_as(seat_id):
                told.append((seat_id, module.say_once(SayOnce("causes:plague"))))
        self.assertEqual(told, [("alpha", True), ("beta", True), ("alpha", False), ("beta", False)])


class CausesFailTold(unittest.TestCase):

    def test_each_seat_whose_causes_fail_is_told(self):
        module, _ = two_seats()
        module.effective_hazard = lambda event: (None, {"failed": [{"why": "no water", "quantity": "water"}]})
        for seat_id in ("alpha", "beta"):
            with module.needs.act_as(seat_id):
                module.apply_event_causes({"name": "plague"}, 100, 100)
        lines = [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]
        self.assertEqual([line.kind for line in lines], ["hazard_condition_failed", "hazard_condition_failed"])


class ConditionTold(unittest.TestCase):

    def test_each_seat_whose_condition_changes_is_told(self):
        module, _ = two_seats(techniques_held=set())
        hazard = {"name": "plague", "condition": {"requires_all": ["sewers"], "unmet_message": "no sewers"}}
        for seat_id in ("alpha", "beta"):
            with module.needs.act_as(seat_id):
                module.resolve_hazard_condition(hazard, 100, 100)
        lines = [command for command in module_harness.sent(module) if isinstance(command, RecordEvent)]
        self.assertEqual([line.kind for line in lines], ["hazard_condition_unmet", "hazard_condition_unmet"])


class DisasterSummaryPerSeat(unittest.TestCase):

    def test_the_summary_holds_each_seats_own_lines(self):
        module, logs = two_seats(civilisation={"id": "rome", "hazards": [{"name": "Plague", "years": [100, 110]}]})

        def shocks(year, seats):
            logs["alpha"].append((year, "alpha line"))
            logs["beta"].append((year, "beta line one"))
            logs["beta"].append((year, "beta line two"))
        module.shocks = shocks
        module.step_dated_shocks(["alpha", "beta"])
        seen = {}
        for seat_id in ("alpha", "beta"):
            with module.needs.act_as(seat_id):
                seen[seat_id] = module.disaster()["messages"]
        self.assertEqual({seat_id: len(lines) for seat_id, lines in seen.items()}, {"alpha": 1, "beta": 2})


if __name__ == "__main__":
    unittest.main()
