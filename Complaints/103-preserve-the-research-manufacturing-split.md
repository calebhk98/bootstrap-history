# The economy is already separated from research; do not add a blanket manufacturing delay

**Source:** playtest findings document, ECON-001. **Status:** Preserve, not a
defect. It is filed as a complaint because a Preserve finding is as valuable
as a bug report: it stops a future agent from "fixing realism" by adding
something that already exists.

## What the player observed

Across a full Rome run to a hard research goal (junction transistor, completed
in play around year 483), the player repeatedly hit genuine physical
bottlenecks (material capacity, specialist labour, calendar floors) despite
already holding the relevant knowledge. Their conclusion: the model does not
treat "researched" as "manufactured," and it should not be given an
additional generic delay layered on top, because the mechanism already
exists.

## Checked against the current code

`sim/engine/economy_production.py` and the tree schema back this up. A node
already carries, separately:

- `done` (knowledge/completion) versus `operating` (a concern actually
  running),
- capital cost, founder/director hours, specialist labour, material
  quantities and annual material supply/capacity, and electrical power as
  distinct inputs,
- `build_yrs` and `adopt_yrs`, and `treetool.py` computes a node's `yrs` as
  `max(build_yrs, adopt_yrs)`, so construction and adoption run in parallel
  rather than serially,
- failure/retry risk, and a post-opening revenue ramp rather than instant
  full output.

Material consumption is concentrated over build time, not treated as a
single knowledge event. This is the same distinction CLAUDE.md itself asks
for in a different context (§3.1's ban on hardcoded outcomes): the model
already derives "how long until this is actually running" from labour,
material and capital constraints rather than asserting it, which is the
harder and more correct thing to have built.

## The recommendation, and why it is worth stating explicitly

Do not add a universal "N years between research completion and physical
deployment" delay. That would duplicate `build_yrs`/`adopt_yrs`/ramp
mechanics that already exist, would not be derived from anything (a fresh
violation of §3.1 the moment it landed, since it would be exactly the kind
of flat, hand-picked number CLAUDE.md asks agents not to add), and the
player's own experience is evidence it is unnecessary: the run was
*already* slow for physical reasons the model already models.

Where the player's write-up sees real remaining gaps is in the specific
diffusion/economic abstractions (see ECON-002 and LATE-010, filed
separately as `Complaints/104` and `Complaints/116`), not in the
research-to-manufacturing seam itself.

## Cross-references

No existing complaint or `docs/architecture/` document argues for adding a
manufacturing delay, so there is nothing to duplicate here. `ECON-001`'s own
list of what already exists is corroborated directly by the code cited
above; this complaint's only job is to put that corroboration on the record
so nobody re-proposes the same fix without checking first.
