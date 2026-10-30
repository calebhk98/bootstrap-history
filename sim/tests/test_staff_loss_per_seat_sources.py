"""A plague line names the medical work of the seat it is told to, not of the seat acting when the lines are written
(Complaint 741)."""
QUICK_TOPIC = True

import unittest
from contextlib import contextmanager

from sim.reporting.api import RecordEvent
from sim.tests import hazards_host, module_harness
from sim.workforce.api import LoseStaff


class AlwaysHits:
    def random(self):
        return 0.0


class StaffLossPerSeatSources(unittest.TestCase):

    def sources_told(self, built_by_seat):
        """The `national_sources` fact of each seat's plague line; `built_by_seat` maps a seat to the medical node it holds."""
        acting = {"seat": "alpha"}

        @contextmanager
        def act_as(seat_id):
            before, acting["seat"] = acting["seat"], seat_id
            try:
                yield
            finally:
                acting["seat"] = before

        tree = {"herbal": {"name": "Herbal Medicine"}, "sewers": {"name": "Sewers"}}
        module = hazards_host.build(
            act_as=act_as, game_random=AlwaysHits(), tree=tree,
            techniques_held=lambda: {built_by_seat[acting["seat"]]},
            diffusible_ids=lambda category: ("herbal", "sewers"), civ_diffusion=lambda node_id: 0.5,
            diffusion_relief=lambda kind, per_weapon=0.0: 0.3 if kind == "medical" else (1.0, None),
            answers={LoseStaff: lambda command: {"people_before": 10.0, "people_after": 9.0}})
        hazard = {"name": "plague", "staff_loss": 0.2}
        module.staff_loss_seats({"alpha": hazard, "beta": hazard}, 100)
        return {command.seat: command.facts["national_sources"]
                for command in module_harness.sent(module) if isinstance(command, RecordEvent) and command.kind == "hazard_hit"}

    def test_each_seat_is_told_its_own_sources(self):
        told = self.sources_told({"alpha": "herbal", "beta": "sewers"})
        self.assertEqual(told, {"alpha": ["Herbal Medicine"], "beta": ["Sewers"]})


if __name__ == "__main__":
    unittest.main()
