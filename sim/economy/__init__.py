"""The economy: agents that hold money and goods, markets that clear their orders, and the money they pay with.

Standalone. It imports `sim.world` domain models, `sim.constants`, `sim.unit_conversions`, the shared `sim.book`,
`sim.contracts`, `sim.rekey` and `sim.refusal`, and the `sim.geography.api` and `sim.labour.api` surfaces, never `sim.engine`.
Code outside reaches it through `sim/economy/api.py`; the engine does so only in
`sim/markets/port*.py`. Design: docs/architecture/ECONOMY_AGENTS.md.
"""
