# Brayton gas turbine is under-prerequisited

**Type:** Tech-tree realism defect  
**Priority:** High
**Status (project-wide audit, 2026-09-18): RESOLVED, verified.** `en_gas_turbine`'s prerequisites in `data/tech_tree.json` now include `mat_nickel`, `mat_tool_steel_hss`, `thermodynamics_theory` and `air_jet_engine_concept`, closing the gap named here. See `docs/architecture/STATE_OF_THE_PROJECT.md`.

## Player evidence

The project text itself calls for 900+ C operation and a 10+ stage compressor, but visible requirements were only boring mill, 1600 C, and 10 µm tolerance.

## Suggested review

Require appropriate thermodynamics, compressor/aerodynamics, high-temperature/nickel alloy metallurgy, balancing, and manufacturing capability—or revise the description.
