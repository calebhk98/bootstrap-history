"""What built defences take off a hazard, and the one place every figure about it comes from.

hazard_relief_entries lists each defence in force against one kind of harm;
hazard_relief multiplies them; hazard_figure is the harm a hazard does after
them, which the shocks apply and the `risk` and `why` screens print, so a
displayed estimate and an applied one cannot differ. These are methods of
Sim; they are a mixin only so that they can live in a file of their own.
"""
from .hazard_window import hazards_not_yet_past

HAZARD_KINDS = ("staff_loss", "sack_chance", "output_factor", "real_erosion")


class HazardReliefMixin:

    CLOSURE_REASON_WORDS = {
        "staff": "for want of staff",
        "manual": "by your choice",
        "loss_making": "because it was losing money",
        "creditor_seizure": "after creditors seized it",
    }

    def _closure_words(self, node_id):
        record = self.state.projects.closures.get(node_id)
        if record is None:
            return "and has not been opened"
        return self.CLOSURE_REASON_WORDS.get(record["reason"], "")

    def hazard_relief_entries(self, kind, beyond_national=False, assume_running=()):
        """One record per defence that takes something off `kind` of harm.

        Each has the `factor` it multiplies the harm by. `assume_running`
        names nodes to treat as built and running, to price a purchase.
        With `beyond_national`, a technique counts only for the part of the
        country that has not adopted it yet, since national adoption already
        lowered the exposure.
        """
        entries = []
        for node, share, label in self.HAZARD_COUNTERS.get(kind, ()):
            adopted_nationally = 0.0
            lapsed_node = node
            if node == "_own_gold":
                strength = 1.0 if self.mine_capacity.get("gold", 0.0) > 0.0005 else 0.0
            elif node == "_own_silver":
                strength = 1.0 if self.mine_capacity.get("silver", 0.0) > 0.01 else 0.0
            else:
                strength = 1.0 if node in assume_running else self._counter_strength(node)
                for needed in self._counter_requirements(node, kind, label):
                    needed_strength = 1.0 if needed in assume_running else self._counter_strength(needed)
                    if needed_strength < strength:
                        strength, lapsed_node = needed_strength, needed
                if beyond_national and strength > 0.0:
                    adopted_nationally = self.civ_diffusion(node)
            closed = 0.0 < strength < 1.0
            strength *= 1.0 - adopted_nationally
            if strength > 0.0:
                entries.append({
                    "node": None if node.startswith("_") else node, "label": label,
                    "factor": 1.0 - share * strength,
                    "lapsed_node": lapsed_node if closed else None,
                    "partly_adopted_nationally": adopted_nationally > 0.0})
        if kind == "output_factor":
            war_relief, reason = self._military_war_relief()
            if reason:
                entries.append({"node": None, "label": reason, "factor": war_relief})
            state_relief, state_reason = self._state_military_diffusion_relief(
                self.STATE_MIL_RELIEF_CAP_OUTPUT)
            if state_reason:
                entries.append({"node": None, "label": state_reason, "factor": state_relief})
        elif kind == "sack_chance":
            state_relief, state_reason = self._state_military_diffusion_relief(
                self.STATE_MIL_RELIEF_CAP_SACK)
            if state_reason:
                entries.append({"node": None, "label": state_reason, "factor": state_relief})
        return entries

    def _entry_words(self, entry):
        label = entry["label"]
        if entry.get("lapsed_node"):
            label = "%s (lapsed: %s is closed %s)" % (
                label, self.nodes[entry["lapsed_node"]]["name"],
                self._closure_words(entry["lapsed_node"]))
        if entry.get("partly_adopted_nationally"):
            label = "%s (partly adopted nationally)" % label
        return label

    def hazard_relief(self, kind, beyond_national=False, assume_running=()):
        """How much of one kind of harm the things you have built take off.

        Returns (multiplier, [what did it]). Diminishing: each counter removes a
        share of what is LEFT, so five partial answers are strong and none of
        them is a switch that turns history off.
        """
        mult, why = 1.0, []
        for entry in self.hazard_relief_entries(kind, beyond_national, assume_running):
            mult *= entry["factor"]
            why.append(self._entry_words(entry))
        return mult, why

    def mitigation_table(self, kind, base, beyond_national=False):
        """Each defence in force against `kind`, with what it takes off `base`.

        `removes_share` is the share of the unmitigated harm this one defence
        removes given all the others; `points` is that share of `base`, in the
        hazard's own unit. A closed concern's residual relief is marked lapsed.
        """
        entries = self.hazard_relief_entries(kind, beyond_national)
        total = 1.0
        for entry in entries:
            total *= entry["factor"]
        table = []
        for index, entry in enumerate(entries):
            others = 1.0
            for other_index, other in enumerate(entries):
                if other_index != index:
                    others *= other["factor"]
            removes = others - total
            row = {"node": entry["node"], "label": self._entry_words(entry),
                   "status": "lapsed" if entry.get("lapsed_node") else "in force",
                   "removes_share": round(removes, 4),
                   "points": round(removes * base, 4) if base is not None else None}
            if entry.get("lapsed_node"):
                lapsed = entry["lapsed_node"]
                row["closed_because"] = self._closure_words(lapsed)
                row["concern_to_open"] = lapsed
                record = self.state.projects.closures.get(lapsed)
                row["how"] = ("restore %s" if record and record["reason"] == self.CLOSED_BY_CHOICE
                              else "open %s") % lapsed
            table.append(row)
        return table

    def national_public_health_sources(self, limit=3):
        """Names of medical work you built that has spread through the country,
        furthest spread first; the whole of the national relief comes from these."""
        projects = self.state.projects
        spread = sorted(((self.civ_diffusion(node_id), node_id)
                         for node_id in self._diffusible_ids("medical")
                         if node_id in projects.done and node_id not in projects.granted),
                        key=lambda pair: (-pair[0], pair[1]))
        return [self.nodes[node_id]["name"] for share, node_id in spread if share > 0.0][:limit]

    def _national_sources_words(self):
        return ", ".join(self.national_public_health_sources()) or "none named"

    def staff_loss_exposure(self, historical, assume_running=()):
        """The staff a household loses to one wave, from the historical rate.

        The country's own public health lowers the rate first; the household's
        own defences then count only where the nation has not adopted them.
        """
        national_relief = self.medical_diffusion_relief()
        before_defences = historical * (1.0 - national_relief)
        relief, why = self.hazard_relief("staff_loss", beyond_national=True,
                                         assume_running=assume_running)
        return {"national_relief": national_relief, "before_defences": before_defences,
                "relief": relief, "why": why, "loss": before_defences * relief}

    def output_floor(self, hazard_factor, relief):
        """The lowest the output factor falls in a hazard year; relief moves
        the floor back toward 1.0 rather than scaling the damage."""
        return 1.0 - (1.0 - hazard_factor) * relief

    def hazard_figure(self, kind, hazard, assume_running=()):
        """The harm `hazard` does of `kind` after what is built: the fraction of
        staff lost, the yearly sack chance, the output floor, or the erosion."""
        if kind == "staff_loss":
            return self.staff_loss_exposure(hazard[kind], assume_running)["loss"]
        relief = self.hazard_relief(kind, assume_running=assume_running)[0]
        if kind == "output_factor":
            return self.output_floor(hazard[kind], relief)
        return hazard[kind] * relief

    def hazard_effect_preview(self, node_id):
        """For each hazard ahead that building `node_id` would soften: the
        figure now and with it running, from hazard_figure."""
        kinds = {kind for kind, rows in self.HAZARD_COUNTERS.items()
                 for counter_node, _share, _label in rows if counter_node == node_id}
        if not kinds or self._counter_strength(node_id) >= 1.0:
            return []
        out = []
        for hazard, year_start, year_end, _in_progress in hazards_not_yet_past(self.civ, self.year):
            for kind in HAZARD_KINDS:
                if kind in kinds and kind in hazard:
                    now = round(self.hazard_figure(kind, hazard), 4)
                    with_it = round(self.hazard_figure(kind, hazard, (node_id,)), 4)
                    if with_it != now:
                        out.append({"name": hazard.get("name", "hazard"), "kind": kind,
                                    "years": [year_start, year_end],
                                    "now": now, "with_it": with_it})
        return out
