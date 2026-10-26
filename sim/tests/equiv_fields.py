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
]

IGNORED = [
    ("/modules", "module world slots: empty until a module owns state, then each moved field is relocated"),
    ("/seats/*/modules", "module seat slots, likewise"),
    ("/assembly_record", "which modules wrote the game; bookkeeping, not simulation"),
]
