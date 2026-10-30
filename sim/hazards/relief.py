"""What built defences take off a hazard, and the one place every figure about it comes from.

`hazard_relief_entries` lists each defence in force against one kind of harm; `hazard_relief` multiplies them;
`hazard_figure` is the harm a hazard does after them, which the shocks apply and the screens print, so a displayed
estimate and an applied one cannot differ.

Needs: hazard_counter_rows, techniques_held, techniques_granted, running, tree, tree_nodes, mine_capacity,
counter_supply_gap, civ_diffusion, diffusible_ids, diffusion_relief, military_leverage, closure_record, closed_by_choice,
civilisation, year."""
from typing import Any, Dict, List, Optional, Sequence, Tuple

from sim.diffusion.api import constants as diffusion_constants

from . import constants, rules
from .window import hazards_not_yet_past

OWN_MINE_FLOORS = {"_own_gold": ("gold", 0.0005), "_own_silver": ("silver", 0.01)}   # pseudo-source -> (metal, tonnes a year)


class Relief:

	def hazard_counters(self) -> Dict[str, list]:
		"""{kind: [(node or pseudo-source, share, label)]}: what each kind of harm is countered by. The mechanics module
		answers the node entries; the two own-mine sources are not nodes and their shares are declared here."""
		rows = self.needs.hazard_counter_rows()
		cached = self._counters_cache
		if cached is not None and cached[0] is rows:
			return cached[1]
		own = {"real_erosion": [(0, "_own_gold", constants.HAZARD_EROSION_OWN_GOLD, "your own gold, dug not minted"),
		                        (1, "_own_silver", constants.HAZARD_EROSION_OWN_SILVER, "your own silver")]}
		counters = rules.counters_by_kind(rows, own)
		self._counters_cache = (rows, counters)
		return counters

	def counter_strength(self, node: str) -> float:
		"""Fraction of a counter's relief in force: none if never built, full while it is knowledge or a running
		concern, a residue once a concern has been closed."""
		if node not in self.needs.techniques_held():
			return 0.0
		return rules.counter_strength(True, self.needs.running[node], constants.KNOWLEDGE_RESIDUE_AFTER_CLOSURE)

	def hazard_relief_entries(self, kind: str, beyond_national: bool = False, assume_running: Sequence[str] = ()) -> List[Dict[str, Any]]:
		"""One record per defence that takes something off `kind` of harm, each with the `factor` it multiplies the harm by.
		`assume_running` names nodes to treat as built and running, to price a purchase. With `beyond_national`, a
		technique counts only for the part of the country that has not adopted it yet."""
		entries = []
		for node, share, label in self.hazard_counters().get(kind, ()):
			adopted_nationally = 0.0
			lapsed_node, short_of, closed = node, None, False
			if node in OWN_MINE_FLOORS:
				metal, floor = OWN_MINE_FLOORS[node]
				strength = rules.own_mine_strength(self.needs.mine_capacity().get(metal, 0.0), floor)
			else:
				strength = 1.0 if node in assume_running else self.counter_strength(node)
				for needed in rules.counter_requirements(self.needs.tree[node], kind, label):
					needed_strength = 1.0 if needed in assume_running else self.counter_strength(needed)
					if needed_strength < strength:
						strength, lapsed_node = needed_strength, needed
				closed = 0.0 < strength < 1.0
				if strength > 0.0:
					supply, short_of = self.needs.counter_supply_gap(node, kind, label)
					strength = min(strength, supply)
				if beyond_national and strength > 0.0:
					adopted_nationally = self.needs.civ_diffusion[node]
			strength *= 1.0 - adopted_nationally
			if strength > 0.0 or short_of:
				entries.append({
					"node": None if node.startswith("_") else node, "label": label,
					"factor": 1.0 - share * strength,
					"lapsed_node": lapsed_node if closed else None,
					"short_of": short_of,
					"partly_adopted_nationally": adopted_nationally > 0.0, "source": "counter"})
		if kind == "output_factor":
			war_relief, reason = rules.war_relief(self.needs.military_leverage(), constants.MILITARY_WAR_RELIEF_CAP)
			if reason:
				entries.append({"node": None, "label": reason, "factor": war_relief, "source": "own_military_strength"})
			state_relief, state_reason = self.needs.diffusion_relief("military", diffusion_constants.STATE_MIL_RELIEF_PER_WEAPON_OUTPUT)
			if state_reason:
				entries.append({"node": None, "label": state_reason, "factor": state_relief, "source": "state_weapons"})
		elif kind == "sack_chance":
			state_relief, state_reason = self.needs.diffusion_relief("military", diffusion_constants.STATE_MIL_RELIEF_PER_WEAPON_SACK)
			if state_reason:
				entries.append({"node": None, "label": state_reason, "factor": state_relief, "source": "state_weapons"})
		return entries

	def _closure_words(self, node_id: str) -> str:
		return rules.closure_words(self.needs.closure_record[node_id], constants.CLOSURE_REASON_WORDS)

	def _entry_words(self, entry: Dict[str, Any]) -> str:
		lapsed = entry.get("lapsed_node")
		if not lapsed:
			return rules.entry_words(entry, None, None)
		return rules.entry_words(entry, self.needs.tree[lapsed]["name"], self._closure_words(lapsed))

	def hazard_relief(self, kind: str, beyond_national: bool = False, assume_running: Sequence[str] = ()) -> Tuple[float, List[str]]:
		"""How much of one kind of harm the things you have built take off: (multiplier, [what did it]). Diminishing: each
		counter removes a share of what is LEFT, so five partial answers are strong and none is a switch that turns
		history off."""
		multiplier, why, _lapsed = self.hazard_relief_detail(kind, beyond_national, assume_running)
		return multiplier, why

	def hazard_relief_detail(self, kind: str, beyond_national: bool = False, assume_running: Sequence[str] = ()
			) -> Tuple[float, List[str], List[str]]:
		"""hazard_relief's (multiplier, [what did it]) and the names of the closed concerns whose relief lapsed."""
		multiplier, why, lapsed = 1.0, [], []
		for entry in self.hazard_relief_entries(kind, beyond_national, assume_running):
			multiplier *= entry["factor"]
			why.append(self._entry_words(entry))
			if entry.get("lapsed_node"):
				lapsed.append(self.needs.tree[entry["lapsed_node"]]["name"])
		return multiplier, why, lapsed

	def mitigation_table(self, kind: str, base: Optional[float], beyond_national: bool = False) -> List[Dict[str, Any]]:
		"""Each defence in force against `kind`, with what it takes off `base`. `removes_share` is the share of the
		unmitigated harm this one defence removes given all the others; `points` is that share of `base`, in the hazard's
		own unit. A closed concern's residual relief is marked lapsed."""
		entries = self.hazard_relief_entries(kind, beyond_national)
		removed = rules.removed_shares(entries)
		table = []
		for entry, removes in zip(entries, removed):
			row = {"node": entry["node"], "label": self._entry_words(entry),
			       "status": "lapsed" if entry.get("lapsed_node") or entry.get("short_of") else "in force",
			       "removes_share": round(removes, 4),
			       "points": round(removes * base, 4) if base is not None else None}
			if entry.get("lapsed_node"):
				lapsed = entry["lapsed_node"]
				row["closed_because"] = self._closure_words(lapsed)
				row["concern_to_open"] = lapsed
				record = self.needs.closure_record[lapsed]
				row["how"] = ("restore %s" if record and record["reason"] == self.needs.closed_by_choice() else "open %s") % lapsed
			table.append(row)
		return table

	def national_public_health_sources(self, limit: int = 3) -> List[str]:
		"""Names of medical work you built that has spread through the country, furthest spread first; the whole of the
		national relief comes from these."""
		held, granted = self.needs.techniques_held(), self.needs.techniques_granted()
		spread = sorted(((self.needs.civ_diffusion[node_id], node_id) for node_id in self.needs.diffusible_ids["medical"]
		                 if node_id in held and node_id not in granted),
		                key=lambda pair: (-pair[0], pair[1]))
		return [self.needs.tree[node_id]["name"] for share, node_id in spread if share > 0.0][:limit]

	def staff_loss_exposure(self, historical: float, assume_running: Sequence[str] = ()) -> Dict[str, Any]:
		"""The staff a household loses to one wave, from the historical rate. The country's own public health lowers the
		rate first; the household's own defences then count only where the nation has not adopted them."""
		national_relief = self.needs.diffusion_relief("medical")
		relief, why, lapsed = self.hazard_relief_detail("staff_loss", beyond_national=True, assume_running=assume_running)
		figures = rules.staff_exposure(historical, national_relief, relief)
		return {**figures, "why": why, "lapsed_hedges": lapsed}

	def hazard_figure(self, kind: str, hazard: Dict[str, Any], assume_running: Sequence[str] = ()) -> float:
		"""The harm `hazard` does of `kind` after what is built: the fraction of staff lost, the yearly sack chance, the
		output floor, or the erosion."""
		if kind == "staff_loss":
			return self.staff_loss_exposure(hazard[kind], assume_running)["loss"]
		relief = self.hazard_relief(kind, assume_running=assume_running)[0]
		if kind == "output_factor":
			return rules.output_floor(hazard[kind], relief)
		return hazard[kind] * relief

	def hazard_effect_preview(self, node_id: str) -> List[Dict[str, Any]]:
		"""For each hazard ahead that building `node_id` would soften: the figure now and with it running."""
		kinds = {kind for kind, rows in self.hazard_counters().items()
		         for counter_node, _share, _label in rows if counter_node == node_id}
		if not kinds or self.counter_strength(node_id) >= 1.0:
			return []
		preview = []
		for hazard, year_start, year_end, _in_progress in hazards_not_yet_past(self.needs.civilisation(), self.needs.year()):
			for kind in constants.HAZARD_KINDS:
				if kind in kinds and kind in hazard:
					now = round(self.hazard_figure(kind, hazard), 4)
					with_it = round(self.hazard_figure(kind, hazard, (node_id,)), 4)
					if with_it != now:
						preview.append({"name": hazard.get("name", "hazard"), "kind": kind, "years": [year_start, year_end],
						                "now": now, "with_it": with_it})
		return preview
