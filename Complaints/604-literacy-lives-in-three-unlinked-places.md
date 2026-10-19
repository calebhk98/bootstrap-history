# Literacy lives in three unlinked places and gates hiring, not research output

**Status:** open

Part of Complaint 489 (Population is one national figure, and soldiers, scholars and builders are not checked against food and people).

Related: 490 and 491.

**What is wrong.** Literacy is a civilisation field, a stratum `literacy` and a technology effect, with nothing linking them, and it gates hiring but not research output.

**Evidence.** `sim/labour/labour_capacity.py`, `sim/agents/stratum_year.py`.

**Why it matters.** A state's research and administration should follow from how many can read.

**What it would take.** One literacy state per country, read by training and by research.

**Test.** A test raises a country's literacy: hiring and research output both read the same value; `grep` shows one source of literacy.
