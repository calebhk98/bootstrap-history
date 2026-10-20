# A foreign country has no disease: the disease port steps one patch, the home nation

**Status:** closed. Each foreign country holds its own epidemics on its profile (`disease_records`, `disease_introduced`, `disease_deaths`) and runs the home nation's year (`sim/disease/nation.py`, shared with `sim/engine/disease_port.py`) from `sim/agents/country_disease.py`; the deaths enter its `Population.step`. A pathogen arrives by the home contact rule (the profile's `extra["disease_exposure"]` windows) and by contact from any country where it circulates (`DISEASE_CONTACT_ANNUAL_CHANCE`, no routes yet). Not yet: technology relief abroad, contact with the home nation, route-based contact. Test: `country_disease`.

Part of Complaint 482 (Countries other than the home one are static stubs).

Depends on 590. Shares ground with 490 (disease is one patch, and old plagues are dated); this piece only makes the patch per country, and 490 keeps the dated-plague question.

**What is wrong.** Disease is stepped for one patch, so plague cannot arise, spread or die out abroad.

**Evidence.** `sim/engine/disease_port.py` steps one patch: the home nation.

**Why it matters.** Plague and its mortality are part of the outcome the baseline must draw from an ensemble (CLAUDE.md 4.2), and every country needs the same rules.

**What it would take.** A disease patch per country stepped by the same port, with mortality applied to that country's `Population` (590). Read 490 first so the two do not duplicate work.

**Test.** A fixture with an infection seeded in a foreign country raises that country's deaths and leaves another country's unchanged.
