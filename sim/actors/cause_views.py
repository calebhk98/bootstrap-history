"""Plain figures of the state and the home bodies of people that other modules judge (the hazards module's event causes)."""
from typing import Any, Dict, List


class CauseViews:
	"""Mixed into `Actors`."""

	needs: Any

	def state_budget_figures(self) -> Dict[str, float]:
		"""What the acting seat's government needs and cannot fund, summed over its lines, and the share of the opening metal
		its coin still holds."""
		record = self.state_treasury().record  # type: ignore[attr-defined]
		return {"need": sum(record.need.values()), "unfunded": sum(record.unfunded.values()),
		        "coin_metal_kept": float(record.coin_metal_kept)}

	def army_figures(self) -> Dict[str, float]:
		"""Soldiers the state's threat calls for and soldiers it keeps."""
		world = self.actor_world()  # type: ignore[attr-defined]
		return {"wanted": world.army_wanted(), "under_arms": world.soldiers_under_arms()}

	def state_knows(self, node_id: str) -> bool:
		"""Whether the acting seat's government holds the technology."""
		return bool(self.state_treasury().knows(node_id, self.actor_world()))  # type: ignore[attr-defined]

	def home_strata_rows(self) -> List[Dict[str, Any]]:
		"""One row per home body of people still in the country: members, bonded, welfare (None until a yearly welfare is
		measured), and the share and property share its opening plan gave it."""
		return [{"members": stratum.record.members, "bonded": bool(stratum.record.plan.get("bonded")),
		         "welfare": stratum.record.welfare if stratum.record.welfare_reference > 0.0 else None,
		         "opening_share": float(stratum.record.plan.get("share", 0.0)),
		         "property_share": float(stratum.record.plan.get("property_share", 0.0))}
		        for stratum in self.cast().of_kind("stratum")  # type: ignore[attr-defined]
		        if stratum.record.country is None and stratum.record.exited_year is None]
