# A higher tax rate has no consequence beyond revenue and a typed burden weight

**Status:** open

Follows from 626 (tax rates as a state choice).

**What is wrong.** A state can raise the rate of a form (a player's lever, or an AI state's `raise_rate` response), and the
form yields more of the same base. Nothing else follows from the higher rate: the taxed base does not shrink, hide, move
or stop being worked, and compliance does not wear down. The AI state weighs a raise only by `FISCAL_BURDEN_WEIGHT`
(`sim/agents/tuning_fiscal.py`), a typed heuristic, so it will keep raising a rate as far as the shortfall asks, up to the
yearly step. A rate that costs nothing but a weight is still an input, not an outcome.

**Evidence.** `sim/agents/fiscal_response.py` (`menu`, the `raise_rate` option); `sim/agents/revenue.py` (the base does not
read the rate); `concealed` and `defiance` on `ActorRecord` are set by demand answers, not by the rate.

**Why it matters.** Without a response of the base, there is no ceiling to taxation but the rate cap, and no way a state
loses by overtaxing (CLAUDE.md 4.1: the outcome should come from lower-level state, not from a typed elasticity).

**What it would take.** A mechanism for how taxpayers respond to the share taken: concealment of income and land,
migration out of a taxed tile, withdrawal of labour, from the payers' own choices (households and firms compare what they
keep with what they could keep elsewhere), not a typed elasticity. Then the AI state values the loss of base as a consequence
of a raise, and `FISCAL_BURDEN_WEIGHT` retires.

**Test.** A test: raising a rate on a base whose payers can conceal or leave lowers the base next year; an AI state with the
loss in its menu raises a rate less than one without.
