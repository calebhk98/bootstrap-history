# A foreign country has no disease: the disease port steps one patch, the home nation

**Status:** open

Part of Complaint 482 (Countries other than the home one are static stubs).

Depends on 590. Shares ground with 490 (disease is one patch, and old plagues are dated); this piece only makes the patch per country, and 490 keeps the dated-plague question.

**What is wrong.** Disease is stepped for one patch, so plague cannot arise, spread or die out abroad.

**Evidence.** `sim/engine/disease_port.py` steps one patch: the home nation.

**Why it matters.** Plague and its mortality are part of the outcome the baseline must draw from an ensemble (CLAUDE.md 4.2), and every country needs the same rules.

**What it would take.** A disease patch per country stepped by the same port, with mortality applied to that country's `Population` (590). Read 490 first so the two do not duplicate work.

**Test.** A fixture with an infection seeded in a foreign country raises that country's deaths and leaves another country's unchanged.
