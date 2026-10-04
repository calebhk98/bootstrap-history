# Deposits have no geology layer

**Status:** open

Undiscovered deposits (`sim/geography/resources_endowment.py`) are spread by a permissiveness built from climate group, elevation spread and nearness to known deposits, because the map has no geology. Consequences, measurable with `api.endowment(tile, resource)` over all tiles:

- Every tile holds some expected hidden gold (a few tonnes), cratons and sedimentary basins alike.
- Coal, oil and salt are about as likely under a desert as under a temperate basin unless the weights in `data/world/geography/resources/*.json` are tuned, which would be fitting.
- Giant and gem deposit types only exist near catalogued deposits (`provincial_only`), so an uncatalogued province has none.

What it would take: a per-tile geologic province layer (craton, orogen, basin, large igneous province; Hasterok et al. 2022 is a small global vector set) and sediment thickness (CRUST1.0), built by `python3 -m sim.geography.layer_build`, and deposit types' `permissive_when` rewritten against them.
