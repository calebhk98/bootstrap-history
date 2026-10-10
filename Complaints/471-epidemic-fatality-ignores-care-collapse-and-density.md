# Epidemic fatality ignores care collapse, and contact does not scale with density

**Status:** open

The disease model (`sim/disease/`, wired by `sim/engine/disease_port.py`, Complaint 386) scales case fatality by age band and by the nutrition shortfall, but two modifiers in `Complaints/reports/epidemic-model-research.md` sections 2 and 11.3 are not there:

- Care collapse: when many adults are ill at once, nobody nurses them and fatality rises. Nothing raises a band's fatality with the share of the nation infected, so a mass epidemic is no deadlier than a small one at the same age mix and food.
- Density: contact is fully mixed across the whole nation, whatever its urban share or settlement. The report cites sublinear scaling of contact with density (Rader et al. 2020, abstract read); the exponent would be data per pathogen.

Neither has a sourced number in the report, so each needs a labelled heuristic (CLAUDE.md 4.4) varied across the ensemble, or a source found first. Measure the effect with `python3 -m sim.tests --only disease_century` (the century run prints nothing; add the figure) and the slow `disease_ensemble` topic.

Related: 386 (closed).
