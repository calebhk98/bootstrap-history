"""Rewrites and exclusions the equivalence tool applies to the CURRENT checkout's saved state before hashing.

Paths are "/"-joined with a leading "/", list items by index: "/seats/founder/household/capital".
A prefix matches a path equal to it or continuing after a "/".

RELOCATIONS: ordered (current_prefix, base_prefix) pairs: where a field lives now, and where it lived on the base.
A field that moved gets one entry, in the commit that moves it, so it hashes as it did on the base. A `*` segment
matches any one segment (a seat id) and is carried into the base prefix. Applied first, in order, each to the result of the one before.
IGNORED: (prefix, reason) pairs dropped after relocation, for bookkeeping that exists only in the new build
(a new section is not divergence). A relocated field is still compared: it is renamed, not ignored.
This is test tooling, not a save migration.
"""

RELOCATIONS = [
    ("/modules/living_stock/society_herds", "/economy/society_herds"),
    ("/modules/coin/metal_ratios", "/economy/coin_metal_ratios"),
    ("/modules/campaigns/armies", "/economy/campaigns/armies"),
    ("/modules/campaigns/drawn", "/economy/campaigns/drawn"),
    ("/modules/campaigns/held_since", "/economy/campaigns/held_since"),
    ("/modules/campaigns/next_id", "/economy/campaigns/next_id"),
    ("/modules/reporting/output_per_head", "/economy/output_per_head"),
    ("/modules/reporting/introduction_prices", "/economy/introduction_prices"),
    ("/modules/reporting/money_real", "/economy/money_real"),
    ("/modules/reporting/wage_market_ratios", "/economy/wage_market_ratios"),
    ("/modules/reporting/agent_baseline_prices", "/economy/agent_baseline_prices"),
    ("/modules/foreign_trade/market_book", "/economy/foreign_market_book"),
    ("/modules/foreign_trade/actor_trade", "/economy/foreign_actor_trade"),
    ("/modules/foreign_trade/home_actor_trade", "/economy/home_actor_trade"),
    ("/modules/foreign_trade/ledgers", "/economy/foreign_ledger"),
    ("/modules/foreign_trade/trade_by_year", "/economy/foreign_trade_by_year"),
    ("/seats/*/modules/reporting/log", "/seats/*/household/log"),
    ("/seats/*/modules/reporting/automation_audit", "/seats/*/household/automation_audit"),
    ("/modules/agriculture/wild_stock", "/economy/wild_stock"),
    ("/modules/agriculture/soil_nitrogen", "/economy/soil_nitrogen"),
    ("/modules/agriculture/weather_salt", "/scenario/weather_salt"),
    ("/modules/diffusion/technique_first_run", "/economy/technique_first_run"),
    ("/modules/diffusion/technique_record_started", "/economy/technique_record_started"),
    ("/modules/diffusion/literacy_said", "/scenario/_literacy_said"),
    ("/seats/*/modules/diffusion/disclosures", "/seats/*/projects/disclosures"),
    ("/seats/*/modules/knowledge/forgotten", "/seats/*/projects/forgotten"),
    ("/modules/resources/forest_felled", "/economy/forest_felled"),
    ("/seats/*/modules/resources/mines", "/seats/*/holdings/mines"),
    ("/seats/*/modules/resources/mine_pending", "/seats/*/holdings/mine_pending"),
    ("/seats/*/modules/resources/mine_ready", "/seats/*/holdings/mine_ready"),
    ("/seats/*/modules/resources/mine_cost_paid", "/seats/*/holdings/mine_cost_paid"),
    ("/seats/*/modules/resources/mine_tranches", "/seats/*/holdings/mine_tranches"),
    ("/seats/*/modules/resources/deposits_found", "/seats/*/holdings/deposits_found"),
    ("/seats/*/modules/resources/deposit_drawn", "/seats/*/holdings/deposit_drawn"),
    ("/seats/*/modules/resources/prospected_person_days", "/seats/*/holdings/prospected_person_days"),
    ("/seats/*/modules/resources/forest_ha", "/seats/*/holdings/forest_ha"),
    ("/seats/*/modules/resources/nitre_bed_m2", "/seats/*/holdings/nitre_bed_m2"),
    ("/seats/*/modules/materials/shortages", "/seats/*/holdings/shortages"),
    ("/seats/*/modules/materials/throttle", "/seats/*/holdings/throttle"),
    ("/seats/*/modules/materials/binding", "/seats/*/holdings/binding"),
    ("/seats/*/modules/materials/shortage_condition", "/seats/*/holdings/shortage_condition"),
    ("/seats/*/modules/materials/material_demand_at_last_throttle", "/seats/*/holdings/material_demand_at_last_throttle"),
]

IGNORED = [
    ("/modules", "module world slots: empty until a module owns state, then each moved field is relocated"),
    ("/seats/*/modules", "module seat slots, likewise"),
    ("/assembly_record", "which modules wrote the game; bookkeeping, not simulation"),
]
