# Confiscation counts only the purse, so coin lodged with another actor escapes it for free

**Status:** open

A mod can shelter coin from fire, sack, banditry, plague and debasement by moving it through the ledger to another
actor (`mods/bh_cashshelter_z6f2`). It cannot make the state count that coin. `answer_confiscation`
(`sim/engine/state_demand.py:33`) demands a share of `visible_wealth(household.capital, household.concealed)` and
takes the payment with `lose_capital` from the purse only; both confiscation callers use it
(`sim/engine/society_state_pressure.py:1344`, `sim/engine/core_step_phases.py:501`). Any claim the household holds
on another actor (a deposit, a loan, a letter of credit) is invisible to the treasury and cannot be taken.

Why it matters: lodging coin with a holder both shelters it and hides it from the state, which is stronger than
the real world, where a deposit with a known temple or banker is the first thing a treasury reaches. The shelter is
then not paid for in the one hazard it most defeats. The same gap applies to a loan or a share held by any actor.

What it would take: a way for a mechanism to declare what an actor is owed by others, which the confiscation share
counts and takes once the purse is empty.

Proof of concept: branch `engine-confiscation-counts-claims`. It adds `register_wealth_claims(reader, seizer)` and
`WEALTH_CLAIMS` in `sim/engine/state_demand.py`: `answer_confiscation` adds the readers' sum to the wealth it
demands a share of, takes from the purse first, then calls each seizer for the rest (money goes to the treasury).
With nothing registered the behaviour is unchanged. Regression test:
`sim/tests/test_confiscation_counts_claims.py`. The mod registers its claims with it when the function exists.
Not done there: concealment of claims, the stance of the holder, and a state that can reach only claims in its own
country.
