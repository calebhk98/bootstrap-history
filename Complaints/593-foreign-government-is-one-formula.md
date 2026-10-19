# ForeignGovernment is one revenue formula: no revenue forms, works, navy, dole, reserve policy or borrowing

**Status:** open

Part of Complaint 482 (Countries other than the home one are static stubs).

Depends on 590 (earners counted). Blocks 594 and 595.

**What is wrong.** `ForeignGovernment.revenue` is earners times labourer pay times tax share times capacity, and the state pays army and officials only.

**Evidence.** `sim/agents/government_foreign.py`; the home `Government` has revenue forms, works, navy, dole, reserve policy and borrowing (`sim/agents/budget.py` `standing_lines`, `sim/agents/revenue.py`).

**Why it matters.** A country's revenue and war capacity are inputs, not outcomes, and a player cannot hold a country whose state is one formula (481).

**What it would take.** Retire `ForeignGovernment` in favour of a country-scoped `Government` whose revenue forms come from that country's civilisation file. Delete the class, do not wrap it.

**Test.** `grep -rn ForeignGovernment sim` is empty; a foreign country's revenue is assessed from its declared forms in `data/civilizations/`; the home `Government` topics pass unchanged for a non-home country.
