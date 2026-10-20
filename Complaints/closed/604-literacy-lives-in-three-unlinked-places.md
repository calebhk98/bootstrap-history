# Literacy lives in three unlinked places and gates hiring, not research output

**Status:** closed - current literacy is owned by strata and read by hiring and research

Part of Complaint 489 (Population is one national figure, and soldiers, scholars and builders are not checked against food and people).

Related: 490 and 491.

**What is wrong.** Literacy is a civilisation field, a stratum `literacy` and a technology effect, with nothing linking them, and it gates hiring but not research output.

**Evidence.** `sim/labour/labour_capacity.py`, `sim/agents/stratum_year.py`.

**Why it matters.** A state's research and administration should follow from how many can read.

**What it would take.** One literacy state per country, read by training and by research.

**Test.** A test raises a country's literacy: hiring and research output both read the same value; `grep` shows one source of literacy.

**Resolution.** `sim/agents/literacy.py` derives country reading shares from living strata.
Schooling and technology teach those records; hiring, research, diffusion and the screens
read the same view. Civilisation/profile literacy is opening data, and live civilisation
and save metadata no longer carry independent totals. See `sim/agents/LITERACY.md`.

Run `python3 -m sim.tests --only country_literacy,country_literacy_totals` for country
isolation, hiring and research progress, schooling reach, migration and save round-trips.
