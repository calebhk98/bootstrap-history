# Epidemic fatality ignores care collapse, and contact does not scale with density

**Status:** closed - care collapse and density scaling of contact are in the disease model, both labelled heuristics

The disease model (`sim/disease/`, wired by `sim/engine/disease_port.py`, Complaint 386) scales case fatality by age band and by the nutrition shortfall, but two modifiers in `Complaints/reports/epidemic-model-research.md` sections 2 and 11.3 are not there:

- Care collapse: when many adults are ill at once, nobody nurses them and fatality rises. Nothing raises a band's fatality with the share of the nation infected, so a mass epidemic is no deadlier than a small one at the same age mix and food.
- Density: contact is fully mixed across the whole nation, whatever its urban share or settlement. The report cites sublinear scaling of contact with density (Rader et al. 2020, abstract read); the exponent would be data per pathogen.

Neither has a sourced number in the report, so each needs a labelled heuristic (CLAUDE.md 4.4) varied across the ensemble, or a source found first. Measure the effect with `python3 -m sim.tests --only disease_century` (the century run prints nothing; add the figure) and the slow `disease_ensemble` topic.

Related: 386 (closed).

Closed (branch close-471-care-collapse-and-density):
- Care collapse: `sim/disease/step.py` multiplies a step's case fatality by one plus a sensitivity times the ill share of the caregiving bands (`care_collapse_multiplier`). The engine passes the working-age band and `DISEASE_CARE_COLLAPSE_SENSITIVITY` (`sim/engine/disease_port.py`, a declared temporary heuristic; no figure found in the report, Neel 1970 is the direction only).
- Density: each pathogen file carries `density_exponent` (required, validated between 0 and 1, tagged `unsourced` with the Rader et al. 2020 range as its reasoning). `advance_year` scales transmission by the nation's crowding index to that power; the index comes from the civilisation's urban share and `DISEASE_URBAN_DENSITY_RATIO` (declared heuristic, retired when the spatial stage lands).
- Measure: `python3 -m sim.tests --only disease_century` prints the deepest fall in 75 years with each modifier off and on, and asserts both raise deaths and the fall with both stays inside the published span. Quick tests are in `test_disease_wiring.py`.
