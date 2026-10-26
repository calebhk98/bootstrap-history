"""Rewrites and exclusions the equivalence tool applies to the CURRENT checkout's saved state before hashing.

Paths are "/"-joined with a leading "/", list items by index: "/seats/founder/household/capital".
A prefix matches a path equal to it or continuing after a "/".

RELOCATIONS: ordered (old_prefix, new_prefix) pairs. A field that moved gets one entry, in the commit that
moves it, so it hashes as it did on the base. Applied first, in order, each to the result of the one before.
IGNORED: (prefix, reason) pairs dropped after relocation, for bookkeeping that exists only in the new build
(a new section is not divergence). A relocated field is still compared: it is renamed, not ignored.
This is test tooling, not a save migration.
"""

RELOCATIONS = []

IGNORED = []
