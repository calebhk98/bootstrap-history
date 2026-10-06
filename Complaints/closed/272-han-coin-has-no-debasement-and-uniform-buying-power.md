# Han coin keeps uniform buying power across three centuries

**Status:** closed - a struck-coin state short of its need cuts the metal in its coin and the economy applies the cut each year (`sim/tests/test_state_debases_coin.py`); domestic money prices fixed at load do not follow yet, and dated hazards stay by owner decision

Source: `Complaints/reports/playthrough-review-han-china-100-to-400ad.md`, item 4 (currency debasement).

## What is wrong

Rome's data names debasement events (`grep -il debas data/civilizations/*.json` lists Rome and one other file whose note says its coin was not debased); Han China's has none. In a Han game a coin's buying power never moves, although the period saw severe monetary disorder (melted statues, debased issues in the successor states). The review calls it nothing in the game.

## Why it matters

Coin that never loses value removes a hazard the founder should plan around, and tilts every wealth decision. `184` records that Rome's dated debasement is a stopgap until debasement falls out of the economy.

## What it would take

Do not add a Han debasement date. Let debasement come from a state that mints against its purse (`docs/architecture/ACTORS_NEXT.md`, the state's spending) and from the coin metal's value (see 135, 140: the price solver's numeraire is labour, not the coin, so a coin that moves while labour does not is representable). Related: 180, 105, 109.

## Remains

Debasement stays a dated hazard in the civilisation data by owner decision, so no Han schedule or state-driven debasement was added here. The state-policy version is future work. A first design for it: a state short of its need after the borrowing ceiling (`sim/agents/government.py`, `pay_standing_need`) strikes the shortfall as lighter coin; the metal in the average coin falls by the cut over the share of the stock replaced, and the price level follows through the coin standard. It needs one more mechanism first: domestic money prices (tree nodes, book constants) are fixed in the opening coin at load, so only wages and traded prices could follow a mid-game change.

Owner decision (2026-10-02): do after the economy is fixed; the engine should gain the capability for a state to debase, the schedule matters little.

## State decision built; economy port to build

Built (agent E, round 2): `debasement_decision(government, world) -> share` in `sim/agents/government_coinage.py`. Only a state whose civilisation's coin standard regime is struck coin decides anything. After `pay_standing_need` it looks at what its standing need left unfunded (revenue, reserve and credit already spent) and cuts the metal in its coin by the share that the part of the stock struck again would recover, up to a ceiling. Both numbers are declared heuristics in `sim/agents/tuning_coinage.py` (`COIN_RESTRIKE_SHARE_PER_YEAR`, `DEBASEMENT_SHARE_CEILING`). It is recorded on `ActorRecord.coin_cut_share` (this year's cut) and `coin_metal_kept` (share of the opening metal the coin holds after every cut). Tests: `python3 -m sim.tests --only agents_coinage`.

Applied: each year `AgentEconomy.run_year` (`sim/engine/economy_port_year.py`) reads the home government's `coin_cut_share` and calls `Economy.strike_lighter_coin`, which lowers the metal per unit through `currency.debase_by_cut` (the average coin holds the cut over the share struck again, `COIN_RESTRIKE_SHARE_PER_YEAR`, less metal). The mint then pays more coin per unit of bullion, so prices and wages follow through the economy. Any government whose coin is struck coin does this; no civilisation is named. Test: `python3 -m sim.tests --only state_debases_coin`.

Not done: domestic money prices (tree nodes, book constants) are fixed in the opening coin at load, so only wages and traded prices follow a mid-game change.
