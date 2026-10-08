# A node's output is priced at the incumbent route, and the payback floor reads gross revenue

**Status:** partly - the payback floor is a diagnostic (`node_payback_diagnostic`, `simulator.py economy-check --payback`) and never caps revenue; stage 0 (scenario test, `test_economy_innovator_pricing`) and the cutting half of stage 2 (a producer that moves the clearing price chooses its ask against the market's book, `sim/economy/seller_pricing.py`, `seller_offers.py`) are in; remaining (see 468's second-pass findings): capacity judged at the post-expansion price, the engine layer's floor/ceiling ratio, and the two expected failures in the scenario (a steady fall, and dearer incumbents leaving). Owner decision (2026-10-06): a new technique's output starts at the incumbent's price and falls as its maker competes for customers, as an outcome, never a hardcoded rule

Two faults in how a derived concern's earning is judged. A node whose technique is not yet held (Solvay soda at the civilisation's start) sells at the price of the incumbent, dearer, route, so its margin is a monopoly's rather than a competitor's; neither that nor selling at its own cost is derived. And the payback floor (`test_node_revenue`, the pump guard in `test_early_playtest.py`) tests build cost over gross revenue, which counts wages passed through to staff, so a cheap, labour-heavy node (hand papermaking) sits near the floor while netting nothing. Net of derived upkeep is the figure a money pump shows in.

Related: `Complaints/319`, `Complaints/329`, `Complaints/283`.

Related: 140, 295, 317, 318, 335, 337.
