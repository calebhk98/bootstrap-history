"""The economy: agents that hold money and goods, markets that clear their orders, and the money they pay with.

Standalone. It imports `sim.world` domain models and `sim.constants`, never `sim.engine`
(sim/tests/test_economy_imports.py). The engine reaches it only through
`sim/engine/economy_port.py`. Design: docs/architecture/ECONOMY_AGENTS.md.
"""
