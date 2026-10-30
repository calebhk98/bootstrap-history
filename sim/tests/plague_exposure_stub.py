"""A nation for the staff-loss exposure rules: the real hazards module over a table of counters, the nodes built and running,
and the nation's own relief and adoption."""
from sim.tests import hazards_host

HISTORICAL_STAFF_LOSS = 0.28
SANITATION_SHARE = 0.4
PREPAREDNESS_SHARE = 0.3
COUNTERS = {"staff_loss": [(0, "sanitation_antisepsis", SANITATION_SHARE, "sanitation"),
                           (1, "plague_preparedness", PREPAREDNESS_SHARE, "preparedness")]}


class PlagueNation:

    def __init__(self, built=(), running=(), national_relief=0.0):
        operating = set(running)
        self.module = hazards_host.build(
            hazard_counter_rows=COUNTERS, techniques_held=set(built), running=lambda node: node in operating,
            tree=lambda node: {"name": node}, civ_diffusion=lambda node: national_relief,
            diffusion_relief=lambda kind, per_weapon=0.0: national_relief if kind == "medical" else (1.0, None))

    def hazard_relief(self, kind):
        return self.module.hazard_relief(kind)

    def staff_loss_exposure(self, historical):
        return self.module.staff_loss_exposure(historical)

    def survivors_share(self):
        """The share of a household's staff left after one wave of the historical plague."""
        return 1.0 - self.staff_loss_exposure(HISTORICAL_STAFF_LOSS)["loss"]


def sanitised(national_relief):
    """A nation with sanitation built and running, and `national_relief` adopted across the country."""
    return PlagueNation(built=("sanitation_antisepsis",), running=("sanitation_antisepsis",), national_relief=national_relief)


def bare(national_relief):
    """A nation with no household defence of its own."""
    return PlagueNation(national_relief=national_relief)
