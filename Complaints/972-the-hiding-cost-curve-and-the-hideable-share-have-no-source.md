# The hiding-cost curve and the hideable share of income have no source

**Status:** open - needs a source someone opens; nothing in the model is missing

Split from 657 (a tax rate with no consequence, solved: the base answers a raise by hiding, flight, unrest, and the
producers, households and the AI state all net it). What is left is two labelled heuristics in `sim/agents/tuning_evasion.py`:
`HIDEABLE_SHARE_OF_INCOME` (the most of its income a payer can keep off the rolls) and `HIDING_MARGINAL_COST_AT_CEILING`
(what hiding the last unit costs). `sim/agents/evasion.py` turns them into the share a payer hides at a rate and an official
reach; with a penalty in proportion to the tax unpaid (Yitzhaki 1974) they set the whole size of the rate response of hiding.

**Searched, nothing usable opened (2026-11):** web searches for Roman Egypt census and tax evasion (Monson and Scheidel,
*Fiscal Regimes and the Political Economy of Premodern States*, 2015, pp. 229-257, is named as the general introduction but
its text was not reachable; the ResearchGate and academia.edu papers on evasion in Roman Egypt returned HTTP 403 or search
snippets only); pre-modern concealment shares and bribe costs (Mughal, Ming, medieval: only modern evasion studies and
popular essays); Zhang Juzheng's 1581 Ming land survey (opened *Fir and Empire*, Appendix A, "Forests in Tax Data": surveys
"added nearly a quarter more farmland", read there as reregistering forest converted to farmland, and registration figures are
"at best indexes of fiscal acreage"; it does not give a hideable share or a cost of hiding). No source found.

**What it would take.** Open a work that gives, for a pre-modern agrarian state, either the share of land or income found
off the rolls when officials looked harder (cadastral resurveys: Ming 1581, Roman Egypt census cycle, Domesday, Mughal
`zabt`), or what concealment cost payers (fees to scribes and surveyors). Cite author, work, page. Set the two constants
from it, or replace them by the holdings model the `retire` text names. Candidates: Monson and Scheidel (eds.) 2015; Kiser and
Kane on tax farming; papyrological studies of Roman Egypt land declarations.
