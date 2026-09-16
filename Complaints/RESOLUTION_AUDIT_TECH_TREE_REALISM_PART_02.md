# Resolution audit: combined tech-tree realism review, part 02

**Scope:** only `COMBINED_TECH_TREE_REALISM_REVIEW_part_02.md`, rows 10–199.

**Result:** all 190 findings have now been dispositioned in data. The 28
`PLAUSIBLE NOW` findings required no change. The 162 actionable findings are
implemented as 78 explicit Roman starting grants, 33 repaired causal gates, and
51 scope or model corrections.

## Validation standard

A cheap or immediately available project does not count as inherited knowledge.
Every `ALREADY ROMAN` node must occur in Rome's explicit `starting_techs`.
Likewise, a date or civilization name is not a causal gate: the revised graph
uses physical stock, materials, tools, skills, transport, or institutions.

The resolution was checked directly against every row in part 02:

- all 190 reviewed IDs resolve in `data/tech_tree.json`;
- all 78 `ALREADY ROMAN` IDs are explicit Rome grants;
- every one of the 33 `MISSING GATE` nodes now has the identified causal parent;
- all 51 `STARTABLE, FIX MODEL` nodes have revised prerequisites, scope,
  description, scale, or institutional requirements; and
- the 28 affirmative findings remain available without artificial date gates.

## Roman inherited knowledge (78 fixed)

The Rome scenario now explicitly grants the ancient textile processes, medical
practices, finance and law, agriculture, construction, navigation, metallurgy,
food processing, and institutions identified by the review. Important examples
include bone setting, employment and apprenticeship contracts, insolvency and
interest regulation, ore preparation, needles, mordant dyeing, composting,
riveting, malting, oil pressing, pile driving, papyrus and parchment, square
rigs, bloomery smelting, lead ship sheathing, textbooks, ferries, and the census.

These are scenario grants only. They were not made ambient or automatically
inherited by Han, Norse, Mexica, or English starts.

## Missing causal gates (33 fixed)

The graph now represents the missing causes rather than historical dates:

- Cashmere, mohair, jute, ramie, hops, pyrethrum, silk cultivation, and guano
  depend on explicit breeding stock, propagation stock, or deposit access.
- Paperclips, safety pins, drawing pins, and sprung mattresses depend on the
  appropriate wire, spring, paper, and precision chains.
- The flyer follows the spinning wheel; pattern grading follows sizing and
  pattern cutting; a spectacle frame follows corrective spectacles.
- Optical codes follow an actual semaphore station; the navigation compass
  follows lodestone knowledge; railway components follow the waggonway/track.
- Degrees, peer review, research groups, examinations, and formal mathematical
  notation now follow their schools, communities, curricula, or mathematics.
- The sternpost rudder follows skeleton-first hull structure.
- Type metal now requires a real antimony supply and type-punch capability.
- Organised whaling now requires specialised boats, harpoons, trained crews,
  whale grounds, and rendering facilities.

Twelve focused supporting nodes model previously absent physical acquisitions
and independent inventions, including silkworm stock, crop stock, antimony
supply, whaling gear, the whippletree, and the nailed horseshoe.

## Startable model and scope findings (51 fixed)

These nodes remain knowledge-transfer projects that can begin as soon as their
real inputs exist, but no longer overclaim what the project delivers:

- Tacit spinning and measurement are separated by making quantified twist rely
  on standards; sizing, straightness, mechanics, momentum, and kinematics also
  use explicit standards and mathematical language.
- Trademark, patent, guild, union, lottery, cartel, bill-of-exchange, funded
  research, and curriculum nodes now model recognition, enforcement, networks,
  staff, or adoption rather than a founder merely writing down an idea.
- Medical barriers follow hand washing and sterile technique; plaster casts
  follow bone setting; vector control no longer bundles later insecticides.
- Generic ancient practices are distinguished from the narrower project:
  casting mould now means repeatable green-sand flask practice, glass mirror
  means a specified reflective backing, and the bilge pump is a shipboard
  adaptation of Rome's force pump.
- The horse-collar bundle is split into a fitted rigid collar, a whippletree,
  and a separately developed nailed horseshoe.
- Separate sewerage is explicitly a district pilot. Grain silos now account for
  moisture, aeration, pests, wall loads, and handling. Skeleton-first hull work
  and these civil projects have costs and durations appropriate to full-scale
  trials rather than bench demonstrations.
- Silver solder no longer claims machine-level joint clearance from Roman hand
  fitting. The balloon description now accounts for envelope and tether mass,
  leakage, heat, and fire. The deeper keel is correctly an improvement to
  windward performance, not its invention.
- Place-value notation is separated from the broader decimal arithmetic
  curriculum, which now represents teaching and institutional adoption.

## Regression protection

`sim/tests/test_realism_part02.py` locks the complete Roman-grant set, each hard
causal edge, the new acquisition nodes, representative bundle splits, and the
absence of Rome-only grant leakage into other civilizations. The existing
explicit-starting-state count was updated from 139 to 217.
