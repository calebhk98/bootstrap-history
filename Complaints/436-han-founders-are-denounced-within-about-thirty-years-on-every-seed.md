# Han founders are denounced within about thirty years on every seed

**Status:** open

Every han_china_100ad scenario in the behaviour fingerprint ends with the founder dead within about 24-34
years, on main (`bcd8b65`) and on the labour branch alike:
- seed 1 ends in year 28 on main and 34 on the branch, "denounced: as a subversive";
- seed 2 ends in year 24 on both.

The other four civilisations run their full 100 or 200 years except for an occasional random event.
Measured with `python3 -m sim.tests.fingerprint check <baseline>` (run lengths), and with a 100-year scratch
run of seed 1 printing `sim.dead_reason`.

Why it matters: when one hazard ends every game for one civilisation within a generation, the hazard is
tuned against it, or it reads a quantity that is out of scale for Han. Complaint 435 shows Han wages two
orders of magnitude apart, so a wealth or visibility measure could be inflated. Either way, the Han
baseline cannot be validated past thirty years.

What it would take: read what drives the denunciation hazard's yearly chance for the Han founder (wealth,
visibility, office?) and compare it with the same quantity in Rome. File the measured cause, or fix it in
the hazard's own package.
