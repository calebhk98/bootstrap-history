# A node's output is priced at the incumbent route, and the payback floor reads gross revenue

**Status:** open, partly done: the payback floor is now a diagnostic (`node_payback_diagnostic`, run with `simulator.py economy-check --payback`) and never caps revenue; what remains is the innovator pricing build. Owner decision (2026-10-06): a new technique's output starts at the incumbent's price and should fall as its maker competes for customers, as an outcome of profit-seeking against demand and rivals, never a hardcoded rule (research first); the payback floor becomes a diagnostic that flags a possible fault and never caps revenue, since a new technique may earn a fortune until its own output drives the price down

Two faults in how a derived concern's earning is judged. A node whose technique is not yet held (Solvay soda at the civilisation's start) sells at the price of the incumbent, dearer, route, so its margin is a monopoly's rather than a competitor's; neither that nor selling at its own cost is derived. And the payback floor (`test_node_revenue`, the pump guard in `test_early_playtest.py`) tests build cost over gross revenue, which counts wages passed through to staff, so a cheap, labour-heavy node (hand papermaking) sits near the floor while netting nothing. Net of derived upkeep is the figure a money pump shows in.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 335, 337.
