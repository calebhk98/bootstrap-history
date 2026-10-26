"""Diffusion's module spec (sim/assembly)."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.polity.api import GainReputation, ShiftValueWeight
from sim.reporting.api import RecordEvent
from sim.workforce.api import NoteTradeSpread, SetEmployed

from .commands import AdvanceSociety, ApplyTechEffects, Disclose, NoteFirstRuns, RekeyDisclosures
from .module import Diffusion
from .state import DiffusionSeat, DiffusionWorld

# Not cached: every one reads the legacy country strata, the tree's live mechanics, the held techniques or the
# government's knowledge, which code outside this module still writes. The disclosure views are cheap lookups that
# hand out the live record, so caching them would need a bump after every in-place edit for no gain.
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "diffusion", Diffusion, world_state=DiffusionWorld, seat_state=DiffusionSeat,
    publishes=(
        ViewSpec("literacy", "literacy", kind=QUOTE, **_LIVE),
        ViewSpec("research_productivity", "research_productivity", kind=QUOTE, **_LIVE),
        ViewSpec("literacy_ceiling", "literacy_ceiling", kind=KEYED, **_LIVE),
        ViewSpec("schooling_flow", "schooling_flow", kind=QUOTE, **_LIVE),
        ViewSpec("effective_schooling_flow", "effective_schooling_flow", kind=QUOTE, **_LIVE),
        ViewSpec("literacy_next_year", "literacy_next_year", **_LIVE),
        ViewSpec("diffusion_share", "diffusion_share", kind=KEYED, **_LIVE),
        ViewSpec("knowledge_half_life_years", "knowledge_half_life_years", kind=QUOTE, **_LIVE),
        ViewSpec("diffusion_index", "diffusion_index", kind=KEYED, **_LIVE),
        ViewSpec("civ_diffusion", "civ_diffusion", kind=KEYED, **_LIVE),
        ViewSpec("diffusible_ids", "diffusible_ids", kind=KEYED, **_LIVE),
        ViewSpec("diffusion_report", "diffusion_report", **_LIVE),
        ViewSpec("diffusion_relief", "diffusion_relief", kind=QUOTE, **_LIVE),
        ViewSpec("foreign_only", "foreign_only", kind=QUOTE, **_LIVE),
        ViewSpec("needs_first", "needs_first", kind=QUOTE, **_LIVE),
        ViewSpec("civ_cost_factor", "civ_cost_factor", kind=QUOTE, **_LIVE),
        ViewSpec("disclosure", "disclosure", kind=KEYED, seat_scoped=True, **_LIVE),
        ViewSpec("disclosures", "disclosures", kind=KEYED, **_LIVE),
        ViewSpec("disclosure_listing", "disclosure_listing", seat_scoped=True, **_LIVE),
        ViewSpec("licensable_actor_ids", "licensable_actor_ids", seat_scoped=True, **_LIVE),
        ViewSpec("copy_difficulty", "copy_difficulty", kind=KEYED, **_LIVE),
        ViewSpec("staff_hire_advice", "staff_hire_advice", kind=QUOTE),
        ViewSpec("staff_sources", "staff_sources", **_LIVE),
        ViewSpec("techniques_spread", "techniques_spread", seat_scoped=True, **_LIVE),
    ),
    applies=((AdvanceSociety, "advance_society"), (ApplyTechEffects, "apply_tech_effects"), (Disclose, "disclose"),
             (NoteFirstRuns, "note_first_runs"), (RekeyDisclosures, "rekey_disclosures")),
    reads=("year", "tree", "tree_nodes", "civilisation", "techniques_held", "techniques_granted", "done_year", "operating",
           "running", "staff", "venture_opened_year", "techniques_in_use", "legacy_country_literacy", "literacy_references",
           "literacy_capacity", "farm_share_of_hours", "trade_spread", "effect_terms", "effect_values",
           "corpus_diffusion_pace", "school_node", "tech_effects", "coverage", "disease_burden", "disease_burden_held",
           "disease_burden_weights", "diffusion_traits", "seat_holders", "built_by_any_seat", "earliest_done_year",
           "state_knowledge", "state_reach", "stock_holds_met", "reputation_gain_of", "seat_list", "seat_party",
           "legacy_actor_registry", "legacy_agent_world"),
    sends=(RecordEvent, ShiftValueWeight, GainReputation, NoteTradeSpread, SetEmployed),
),)
