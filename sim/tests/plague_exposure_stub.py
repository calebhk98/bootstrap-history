"""A nation stub for the staff-loss exposure rules: the real `HazardReliefMixin` arithmetic and the real
`_counter_strength`, over a table of counters, the nodes built and running, and the nation's own relief and adoption."""
from types import SimpleNamespace

from sim.engine.hazard_relief import HazardReliefMixin
from sim.engine.society_hazards import HazardsMixin

HISTORICAL_STAFF_LOSS = 0.28
SANITATION_SHARE = 0.4
PREPAREDNESS_SHARE = 0.3


class PlagueNation(HazardReliefMixin):
    HAZARD_COUNTERS = {"staff_loss": [("sanitation_antisepsis", SANITATION_SHARE, "sanitation"),
                                      ("plague_preparedness", PREPAREDNESS_SHARE, "preparedness")]}
    KNOWLEDGE_RESIDUE_AFTER_CLOSURE = HazardsMixin.KNOWLEDGE_RESIDUE_AFTER_CLOSURE
    _counter_strength = HazardsMixin._counter_strength

    def __init__(self, built=(), running=(), national_relief=0.0):
        self.built, self.operating, self.national_relief = set(built), set(running), national_relief
        self.mine_capacity = {}
        self.state = SimpleNamespace(projects=SimpleNamespace(closures={}))
        self.nodes = {node: {"name": node} for node in ("sanitation_antisepsis", "plague_preparedness")}

    def has(self, node):
        return node in self.built

    def running(self, node):
        return node in self.operating

    def medical_diffusion_relief(self):
        return self.national_relief

    def civ_diffusion(self, node):
        return self.national_relief

    def _counter_requirements(self, node, kind, label):
        return ()

    def counter_supply_gap(self, node, kind, label):
        return 1.0, None

    def survivors_share(self):
        """The share of a household's staff left after one wave of the historical plague."""
        return 1.0 - self.staff_loss_exposure(HISTORICAL_STAFF_LOSS)["loss"]


def sanitised(national_relief):
    """A nation with sanitation built and running, and `national_relief` adopted across the country."""
    return PlagueNation(built=("sanitation_antisepsis",), running=("sanitation_antisepsis",), national_relief=national_relief)


def bare(national_relief):
    """A nation with no household defence of its own."""
    return PlagueNation(national_relief=national_relief)
