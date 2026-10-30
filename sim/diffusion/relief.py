"""What a diffused technique relieves: the country is harder to kill wholesale by disease, and an armed state loses less.

Needs: state_reach, state_knowledge, built_by_any_seat."""
from . import constants
from .diffusion_rules import medical_relief, weapons_relief


class Relief:

    def state_military_weapons_held(self) -> int:
        """How many of the founder's military inventions the government holds."""
        held = self.needs.state_knowledge()
        return sum(1 for node_id in self.needs.built_by_any_seat(self.diffusible_ids("military")) if node_id in held)

    def diffusion_relief(self, kind: str, per_weapon: float = 0.0):
        """What diffusion takes off a harm. "medical": the share of an epidemic's harm relieved, coverage times how
        far people follow the guidance. "military": (multiplier on the harm, reason) for the state holding some of
        the founder's weapons, each removing `per_weapon` of what is left."""
        if kind == "medical":
            return medical_relief(self.diffusion_index("medical"), constants.MEDICAL_COMPLIANCE_BASE, self.needs.state_reach())
        return weapons_relief(per_weapon, self.state_military_weapons_held())
