"""One-line forwarders from `Sim` to the mechanics module, for callers not yet in a module.

Each goes when its last caller reads the view (`sim.view(name)`) itself. The last block is not about mechanics: those
rules read the household, the scenario and the techniques held, and go to their owners (seats, knowledge)."""
from sim.mechanics.api import rules


class ForwardMechanicsMixin:

    def mechanic(self, node_id, name):
        """The parameters `node_id` declares for mechanic `name`, or None."""
        return self.view("mechanic")[name].get(node_id)

    def nodes_with_mechanic(self, name):
        """Sorted ids of every node declaring mechanic `name`."""
        return tuple(self.view("mechanic")[name])

    def running_with_mechanic(self, name):
        return [node_id for node_id, _parameters in self.view("running_mechanics")(name)]

    def _effect_terms(self, channel):
        return self.view("effect_terms")(channel)

    def effect_holds(self, node_id, spec):
        return self.view("effect_holds")(node_id, spec)

    def effect_value(self, node_id, spec):
        return self.view("effect_value")(node_id, spec)

    def effect_values(self, channel):
        return self.view("effect_values")(channel)

    def effect_sum(self, channel, start=0.0):
        return self.view("effect_sum")(channel, start)

    def effect_factor(self, channel, start=1.0, exponent=None):
        return self.view("effect_factor")(channel, start, exponent)

    def effect_best(self, channel):
        return self.view("effect_best")(channel)

    def approval_patron(self, gate):
        return self.view("approval_patron")(gate)

    def school_node(self):
        return self.view("school_node")()

    def patrons_lost_to_eminence(self):
        return self.view("patrons_lost_to_eminence")()

    def corpus_hedge_tiers(self):
        return self.view("corpus_hedge_tiers")()

    def corpus_is_dispersed(self, node_id):
        return self.view("corpus_dispersed")(node_id)

    def corpus_diffusion_pace(self):
        return self.view("corpus_diffusion_pace")()

    def best_corpus_node(self):
        """The corpus node that hedges best, or None if the tree has none."""
        best_first = self.view("corpus_nodes")()
        return best_first[0] if best_first else None

    @property
    def CAPABILITY_INSTITUTIONS(self):
        return self.view("capability_sets")()[0]

    @property
    def SCALABLE_INSTITUTIONS(self):
        return self.view("capability_sets")()[1]

    @property
    def NOT_OPERATING_BENEFIT(self):
        return self.view("capability_sets")()[2]

    @property
    def DISEASE_BURDEN_TECH_IDS(self):
        return tuple(self.view("mechanic")["disease_burden"])

    @property
    def STAFF_CAPACITY_SOURCES(self):
        return self.view("staff_capacity_sources")()

    @property
    def ROOM_SOURCES(self):
        return self.view("room_sources")()

    @property
    def LABOUR_PRODUCTIVITY_SOURCES(self):
        return self.view("labour_productivity_sources")()

    @property
    def HAZARD_COUNTERS(self):
        """{kind: [(node or pseudo-source, share, label)]}: what each kind of harm is countered by.

        The mechanics module answers the node entries; the two own-mine sources are not nodes and their shares are
        declared with the hazards."""
        rows = self.view("hazard_counter_rows")()
        key = (self.HAZARD_EROSION_OWN_GOLD, self.HAZARD_EROSION_OWN_SILVER)
        cached = self.__dict__.get("_hazard_counters_cache")
        if cached is not None and cached[0] is rows and cached[1] == key:
            return cached[2]
        own = {"real_erosion": [(0, "_own_gold", key[0], "your own gold, dug not minted"),
                                (1, "_own_silver", key[1], "your own silver")]}
        counters = rules.hazard_counters(rows, own)
        self.__dict__["_hazard_counters_cache"] = (rows, key, counters)
        return counters

    # ---- not mechanics: awaiting their owners
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
        return self.view("staff")()["directors_extra"] * self.cfg["director_hours_per_year"]

    def deputies_carry_the_work(self):
        """Whether the deputies are enough to go on without the founder."""
        return self.view("staff")()["directors_extra"] >= self.DEPUTIES_CARRY_THE_WORK_FROM

    def founder_age(self):
        return self.cfg["founder_arrival_age"] + self.state.scenario.year - self.cfg["start_year"]
