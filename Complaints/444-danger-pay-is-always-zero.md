# Danger pay is always zero: no trade's fatality risk reaches the economy

**Status:** open - needs data and `sim/engine/economy_port_setup.py`

`sim.economy.labour.reservation_wage` raises the wage asked for a trade by its fatality risk
(`TradeSpec.fatality_risk_per_year`, pinned by `python3 -m sim.tests --only economy_audit_setup`).
The port builds `TradeSpec(trade, training_years)` only (`build_setup`), and `data/world/trades.json`
has no fatality field (`grep -rli fatality data/` finds nothing), so miners are paid like labourers.

What it would take: a sourced yearly fatality risk per trade in `trades.json` (mining, soldiering,
seafaring), and the port passing `fatality_risk_per_year`.
