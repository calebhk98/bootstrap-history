"""Engine behaviour that a technology node asks for through its `mechanics` field.

A node carries `"mechanics": {name: parameters}`; the engine asks "which nodes
declare this mechanic" instead of naming node ids, so a mod that adds, renames
or replaces a node gets the same behaviour by declaring the same mechanic.
The vocabulary is documented in data/branches/VOCABULARY.md.
"""


def nodes_declaring(nodes, name):
    """[(node id, spec)] for nodes declaring mechanic `name`, in (order, id) sequence."""
    found = [(node_id, node["mechanics"][name]) for node_id, node in nodes.items()
             if name in (node.get("mechanics") or {})]
    return sorted(found, key=lambda item: (item[1].get("order", 0), item[0]))


def staff_capacity_sources(nodes):
    """[(node, scholars, artisans, directors, scales_with_units, must_be_running)] from `staff_capacity`."""
    return tuple((node_id, spec.get("scholars", 0.0), spec.get("artisans", 0.0), spec.get("directors", 0.0),
                  spec["scales_with_units"], spec["must_be_running"])
                 for node_id, spec in nodes_declaring(nodes, "staff_capacity"))


class MechanicsMixin:
    """Lookups over the `mechanics` field of the loaded tree."""

    def _mechanics_index(self):
        """{mechanic name: {node id: parameters}}, built once per tree."""
        cached = self.__dict__.get("_mechanics_index_cache")
        if cached is not None and cached[0] is self.nodes:
            return cached[1]
        index = {}
        for node_id in sorted(self.nodes):
            for name, parameters in (self.nodes[node_id].get("mechanics") or {}).items():
                index.setdefault(name, {})[node_id] = parameters
        self.__dict__["_mechanics_index_cache"] = (self.nodes, index)
        return index

    def mechanic(self, node_id, name):
        """The parameters `node_id` declares for mechanic `name`, or None."""
        return self._mechanics_index().get(name, {}).get(node_id)

    def nodes_with_mechanic(self, name):
        """Sorted ids of every node declaring mechanic `name`."""
        return tuple(self._mechanics_index().get(name, {}))

    def running_with_mechanic(self, name):
        """Ids of the nodes declaring `name` that are currently operating."""
        return [node_id for node_id in self.nodes_with_mechanic(name) if self.running(node_id)]

    def _capability_sets(self):
        """(capability ids, scalable ids, {id: lost benefit}), cached with the index."""
        index = self._mechanics_index()
        derived = index.get("\0derived")
        if derived is None:
            capability = index.get("capability", {})
            derived = (
                frozenset(capability),
                frozenset(node_id for node_id, spec in capability.items() if spec.get("scalable")),
                {node_id: spec["lost_benefit"] for node_id, spec in capability.items()
                 if spec.get("lost_benefit")})
            index["\0derived"] = derived
        return derived

    @property
    def CAPABILITY_INSTITUTIONS(self):
        return self._capability_sets()[0]

    @property
    def SCALABLE_INSTITUTIONS(self):
        return self._capability_sets()[1]

    @property
    def NOT_OPERATING_BENEFIT(self):
        return self._capability_sets()[2]

    @property
    def DISEASE_BURDEN_TECH_IDS(self):
        return self.nodes_with_mechanic("disease_burden")

    # ---- effect channels: nodes declare `{channel: {"flat"|"per_unit"|"per_sqrt_unit": v, ...}}`
    def _effect_terms(self, channel):
        """[(node_id, spec)] declaring `channel`, in (order, id) sequence, cached."""
        index = self._mechanics_index()
        key = "\0terms:" + channel
        terms = index.get(key)
        if terms is None:
            specs = index.get(channel, {})
            terms = sorted(specs.items(), key=lambda item: (item[1].get("order", 0), item[0]))
            index[key] = terms
        return terms

    def effect_holds(self, node_id, spec):
        """Whether a declared effect is switched on: operating, or merely built if the spec says gate `has`."""
        return self.has(node_id) if spec.get("gate") == "has" else self.running(node_id)

    def effect_value(self, node_id, spec):
        """The size of one node's effect: flat, or scaled by how much of the institution runs."""
        scale = self.labour.money_per_labour_hour() if spec.get("labour_hours") else 1.0
        if "per_sqrt_unit" in spec:
            return spec["per_sqrt_unit"] * scale * self.institution_units(node_id) ** 0.5
        if "per_unit" in spec:
            return spec["per_unit"] * scale * self.institution_units(node_id)
        return spec["flat"] * scale

    def effect_values(self, channel):
        """[(node_id, value)] for every node whose `channel` effect is switched on, in declared order.

        A spec with `group` counts once per group: the first holder in order.
        """
        out, seen_groups = [], set()
        for node_id, spec in self._effect_terms(channel):
            if not self.effect_holds(node_id, spec):
                continue
            group = spec.get("group")
            if group is not None:
                if group in seen_groups:
                    continue
                seen_groups.add(group)
            out.append((node_id, self.effect_value(node_id, spec)))
        return out

    def effect_sum(self, channel, start=0.0):
        """`start` plus every switched-on effect of `channel`, added one at a time in declared order."""
        total = start
        for _node_id, value in self.effect_values(channel):
            total += value
        return total

    def effect_factor(self, channel, start=1.0, exponent=None):
        """`start` times every switched-on `factor` (or `1 + factor_per_unit_power * units ** exponent`) of `channel`."""
        product = start
        for node_id, spec in self._effect_terms(channel):
            if not self.effect_holds(node_id, spec):
                continue
            if "factor_per_unit_power" in spec:
                product *= 1.0 + spec["factor_per_unit_power"] * self.institution_units(node_id) ** exponent
            else:
                product *= spec["factor"]
        return product

    def effect_best(self, channel):
        """(node_id, spec) of the switched-on `channel` effect with the highest `tier`, or None."""
        best = None
        for node_id, spec in self._effect_terms(channel):
            if self.effect_holds(node_id, spec) and (best is None or spec["tier"] > best[1]["tier"]):
                best = (node_id, spec)
        return best

    def corpus_nodes_best_first(self):
        """Ids of nodes declaring the `corpus` mechanic, highest `rank` first."""
        spec = self._mechanics_index().get("corpus", {})
        return sorted(spec, key=lambda node_id: (-spec[node_id]["rank"], node_id))

    def approval_patron(self, gate):
        """The patron node whose backing lifts the state's `gate` ("wary" or "opposed") on a project, or None."""
        for node_id in self.nodes_with_mechanic("state_approval"):
            if self.mechanic(node_id, "state_approval")["gate"] == gate:
                return node_id
        return None

    def school_node(self):
        """The node whose operation is required for any schooling to happen, or None."""
        for node_id, spec in self._effect_terms("schooling_flow"):
            if spec.get("required"):
                return node_id
        return None

    def patrons_lost_to_eminence(self):
        """Patron nodes an eminent household can lose to a quarrel, highest tier first."""
        return sorted(self.nodes_with_mechanic("patron_lost_to_eminence"),
                      key=lambda node_id: -self.mechanic(node_id, "patron")["tier"])

    def corpus_hedge_tiers(self):
        """[(hedge node, loss chance, fraction lost)], strongest first; corpus_hedge and
        the knowledge-loss warning both read this one rule."""
        return [(node_id, self.mechanic(node_id, "corpus")["loss_chance"],
                 self.mechanic(node_id, "corpus")["fraction_lost"])
                for node_id in self.corpus_nodes_best_first()]

    def corpus_is_dispersed(self, node_id):
        """Whether a corpus node's copies sit beyond one site's reach (a sack cannot take them)."""
        return bool((self.mechanic(node_id, "corpus") or {}).get("dispersed"))

    def dispersed_corpus_running(self):
        return any(self.running(node_id) for node_id in self.nodes_with_mechanic("corpus")
                   if self.corpus_is_dispersed(node_id))

    def losable_node_ids(self, keep_dispersed=True):
        """Built nodes a loss event may take: not inherited, not a measured
        goal (a measurement cannot be forgotten), and by default not a
        dispersed corpus."""
        projects = self.state.projects
        return sorted(node_id for node_id in projects.done
                      if node_id not in projects.granted
                      and not self.nodes[node_id].get("win_condition")
                      and not (keep_dispersed and self.corpus_is_dispersed(node_id)))

    def deputy_hours(self):
        """Hours a year the deputies work, however small a fraction of a deputy."""
        return self.state.household.directors_extra * self.cfg["director_hours_per_year"]

    def deputies_carry_the_work(self):
        """Whether the deputies are enough to go on without the founder."""
        return self.state.household.directors_extra >= self.DEPUTIES_CARRY_THE_WORK_FROM

    def founder_age(self):
        return self.cfg["founder_arrival_age"] + self.state.scenario.year - self.cfg["start_year"]

    def best_corpus_node(self):
        """The corpus node that hedges best, or None if the tree has none."""
        best_first = self.corpus_nodes_best_first()
        return best_first[0] if best_first else None

    def corpus_diffusion_pace(self):
        """Diffusion pace of the best corpus node currently operating (1.0 if none)."""
        for node_id in self.corpus_nodes_best_first():
            if self.running(node_id):
                return self.mechanic(node_id, "corpus")["diffusion_pace"]
        return 1.0

    @property
    def STAFF_CAPACITY_SOURCES(self):
        return staff_capacity_sources(self.nodes)

    @property
    def ROOM_SOURCES(self):
        return tuple((node_id, spec["flat"]) for node_id, spec in self._effect_terms("room_places"))

    @property
    def LABOUR_PRODUCTIVITY_SOURCES(self):
        return tuple((node_id, spec["trade"], spec["bonus"]) for node_id, spec in self._effect_terms("labour_productivity"))

    @property
    def HAZARD_COUNTERS(self):
        """{kind: [(node or pseudo-source, share, label)]}: what each kind of harm is countered by.

        Node entries come from `hazard_counters` lists; the two own-mine sources are not nodes.
        """
        index = self._mechanics_index()
        cached = index.get("\0hazard_counters")
        if cached is None:
            entries = {"real_erosion": [
                (0, "_own_gold", self.HAZARD_EROSION_OWN_GOLD, "your own gold, dug not minted"),
                (1, "_own_silver", self.HAZARD_EROSION_OWN_SILVER, "your own silver")]}
            for node_id, counters in index.get("hazard_counters", {}).items():
                for counter in counters:
                    entries.setdefault(counter["kind"], []).append(
                        (counter["order"], node_id, counter["share"], counter["label"]))
            cached = {kind: [(node, share, label) for _order, node, share, label in sorted(rows)]
                      for kind, rows in entries.items()}
            index["\0hazard_counters"] = cached
        return cached
