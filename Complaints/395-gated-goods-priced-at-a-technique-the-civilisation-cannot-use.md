# A gated good is priced at a technique the civilisation cannot use, so its own route looks unprofitable

**Status:** open

Since every price became solved (`Complaints/123`), a material whose production entries are gated on technology is priced at its mature technique, labelled transitional. With node revenue derived from output (`Complaints/287`), that price reaches what a concern earns. `cementation_steel` now earns nothing: at solved prices its inputs cost more than the steel plate it sells. The likely cause is that steel plate is priced at a later, cheaper steelmaking route that the civilisation does not hold, so the route it does hold looks uneconomic. Found while fixing `sim/tests/test_labour_productivity.py`, whose fixture had relied on this concern earning enough to hire craftsmen.

Why it matters: a price the player cannot act on decides which concerns pay. A Roman cementation works should be priced against what Romans could make steel by, not against a technique centuries away. It also undermines every derived-revenue node whose output is a gated good.

What it would take: price each material for a civilisation at the cheapest technique that civilisation holds or can reach this year (the era gate already exists for the solver; the market's per-civilisation solve should use it), with the mature-technique price only where nothing in reach makes the good, and then say so on screen. Measure with `python3 sim/simulator.py why cementation_steel` and the node revenue table before and after. Related: `Complaints/39` (the solver prices with all of technology available), `Complaints/287`, `Complaints/351`.
