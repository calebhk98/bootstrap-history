"""One-line forwarders from the old `Sim` methods of literacy, diffusion and disclosure to the diffusion module.

The screens, the labour market, the hazards and the agents' port still say `sim.literacy(field)` or
`sim.civ_diffusion(node)`; each line goes when its last caller reads the view or sends the command itself."""
from sim.diffusion.api import AdvanceSociety, ApplyTechEffects, Disclose, NoteFirstRuns, constants

from . import value_weight


class DiffusionForwardsMixin:

    # numbers other topics' code still reads off the game (sim/diffusion/constants.py and value_weight.py declare them)
    STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = constants.STATE_MIL_RELIEF_PER_WEAPON_OUTPUT
    STATE_MIL_RELIEF_PER_WEAPON_SACK = constants.STATE_MIL_RELIEF_PER_WEAPON_SACK
    VALUE_WEIGHT_FLOOR = value_weight.VALUE_WEIGHT_FLOOR
    VALUE_WEIGHT_CEILING = value_weight.VALUE_WEIGHT_CEILING

    # ---- literacy ----

    def country_literacy(self, country=None):
        return self.view("legacy_country_literacy")[country]

    def literacy(self, field, country=None):
        return self.view("literacy")(field, country)

    def research_productivity(self, country=None):
        return self.view("research_productivity")(country)

    def literacy_ceiling_general(self):
        return self.view("literacy_ceiling")["literacy_general"]

    def literacy_ceiling_elite(self):
        return self.view("literacy_ceiling")["literacy_elite"]

    def _schooling_flow(self, field=None):
        return self.view("schooling_flow")(field)

    def effective_schooling_flow(self, field=None):
        return self.view("effective_schooling_flow")(field)

    def literacy_next_year(self):
        return self.view("literacy_next_year")()

    def advance_society(self, year):
        return self.send(AdvanceSociety(year))

    def apply_tech_effects(self, node_id):
        return self.send(ApplyTechEffects(node_id))

    # ---- staff advice ----

    def staff_hire_advice(self, kind, count=None):
        return self.view("staff_hire_advice")(kind, count)

    @property
    def STAFF_SOURCES(self):
        return self.view("staff_sources")()

    # ---- diffusion ----

    def diffusion_share(self, node_id):
        return self.view("diffusion_share")[node_id]

    def knowledge_half_life_years(self, country=None):
        return self.view("knowledge_half_life_years")(country)

    def diffusion_index(self):
        return self.view("diffusion_index")["venture"]

    def information_diffusion_index(self):
        return self.view("diffusion_index")["information"]

    def state_military_diffusion(self):
        return self.view("diffusion_index")["military"]

    def civ_diffusion(self, node_id):
        return self.view("civ_diffusion")[node_id]

    def _diffusible_ids(self, category):
        return self.view("diffusible_ids")[category]

    def medical_diffusion_relief(self):
        return self.view("diffusion_relief")("medical")

    def _state_military_diffusion_relief(self, per_weapon):
        return self.view("diffusion_relief")("military", per_weapon)

    def world_diffusion_report(self):
        return self.view("diffusion_report")()

    def _is_foreign_only(self, node_id):
        return self.view("foreign_only")(node_id)

    def needs_first(self, node_id, about_stock=None):
        return self.view("needs_first")(node_id, about_stock)

    def civ_cost_factor(self, node_id):
        return self.view("civ_cost_factor")(node_id)

    # ---- disclosure ----

    def disclosure_of(self, node_id):
        return self.view("disclosure")[node_id]

    def copy_difficulty(self, node_id):
        return self.view("copy_difficulty")[node_id]

    def disclose(self, node_id, mode, licensee=None, fee=0.0, royalty=0.0):
        return self.send(Disclose(node_id, mode, licensee, fee, royalty))

    def licensable_actor_ids(self):
        return self.view("licensable_actor_ids")()

    def disclosure_listing(self):
        return self.view("disclosure_listing")()

    # ---- which techniques concerns have had time to copy ----

    def techniques_spread(self):
        """The techniques in use that concerns in the same line of business have had time to copy; the techniques
        in use are noted first, so each is stamped with the year it was first seen."""
        self.send(NoteFirstRuns(self.techniques_in_use()))
        return self.view("techniques_spread")()
