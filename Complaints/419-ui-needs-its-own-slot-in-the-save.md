# The UI needs a slot of its own in the save

**Status:** open

What the player writes or sets up through the UI alone (journal notes, extra goals, a standing programme, routes carried into a replay) has nowhere to live in the save. `SimulationState` (`sim/engine/state.py`) is saved field by field from declared dataclasses, so an attribute the UI puts on the `Sim` is lost at the next load, and `sim/ui/` may not edit the engine.

Until then `sim/ui/memory.py` keeps this memory beside the save, in the session sidecar (`<save>.meta.json`, written through `ui_port.settings`), and every save and load the UI makes goes through it, so forks and checkpoints carry it. A save copied or renamed by hand outside the game loses it. Test: `sim/tests/test_ui_memory.py`.

What it would take: one field on `SimulationState`, for example `interface: Dict[str, Any]`, that the engine never reads, plus `interface_memory(sim)` and `set_interface_memory(sim, memory)` in `sim/engine/ui_port.py`. Then only `sim/ui/memory.py` changes: it reads and writes that field instead of the sidecar. The schema inside the dict belongs to the UI (CLAUDE.md 4.6: no migration).

Related: 207, 268, 176, 74, 267.
