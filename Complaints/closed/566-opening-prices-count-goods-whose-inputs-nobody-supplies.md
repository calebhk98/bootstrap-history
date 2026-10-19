# Opening prices include goods whose inputs nobody at the start can supply

**Status:** closed - opening prices keep only goods some runnable recipe makes from priced inputs.

`setup.opening_prices` (`sim/engine/economy_port_setup.py`) prices a good from the engine's table even when
a required input has no price or no supplier at that start. The household need basket then offers it as a
cheap way to meet a need:

    PYTHONPATH=. python3 -c "from sim.engine.economy_port_setup import build_setup; from sim.tests.harness import unopened_sim; s=build_setup(unopened_sim(civ='england_1300')); print(s.opening_prices.get('olive_oil_kg'), s.opening_prices.get('light_oil_lamp'), s.opening_prices.get('light_electric_lamp'))"

England 1300 has no olive oil price yet prices `light_oil_lamp` (its oil input counted as free), and prices
`light_electric_lamp` far below any other light although the node is not held. A basket built on those prices
puts most of England's light spending on the electric lamp. `civ_basket_check.py` already knows which goods a
start cannot supply; the opening prices and the basket should drop them the same way.

`sim/tests/test_lighting_inputs.py` works around it by pricing only goods its territory can supply.

## What it would take

- Leave a good out of `opening_prices` when no recipe it holds, with all inputs supplied, can make it.
- A regression test that England's opening prices carry no electric lamp and no oil lamp.

## Resolution

`build_setup` passes the opening prices through `economy_port_closure.makeable_prices` (`sim/engine/economy_port_closure.py`): a good some production entry makes stays priced only when a recipe the society can run makes it and every input of that recipe is itself still priced. A missing input is not free, a node not held leaves no runnable recipe, and the check repeats until nothing more drops. Goods no entry makes keep their price. The need basket already skips an unpriced good. Tests: `sim/tests/test_opening_price_closure.py`; the lighting spending test now reads the raw opening prices.
