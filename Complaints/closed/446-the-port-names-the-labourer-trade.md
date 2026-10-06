# The economy port names the labourer trade

**Status:** closed - `port_unskilled_trade` (the port takes the unskilled trade from the labour package's fallback trade over `data/world/trades.json`, saves it in the opening values, and passes it as `unskilled_trade`).

The economy reads its unskilled trade and its hunger need from `EconomySetup.unskilled_trade` and
`EconomySetup.hunger_need`, but the port hardcodes `"labourer"` three times in
`sim/engine/economy_port_setup.py` (`opening_values`: `| {"labourer"}`; `coin_per_unit`:
`opening["wages"]["labourer"]`; `build_setup`: `wages.get("labourer", 0.0)`). A civilisation or mod
whose unskilled trade has another name raises a KeyError. The trade should come from civilisation or
trades data and be passed as `unskilled_trade`.
