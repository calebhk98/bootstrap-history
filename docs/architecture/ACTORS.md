# Actors

Who can own money, staff, know-how and works, and decide. Code:
`sim/engine/actors/`. Tests: `sim/tests/test_actors.py`. Tracking:
`Complaints/107-add-independent-firms-imitation-entrepreneurship.md`.

## Class layout

    Actor                     shared surface: money, workforce, knowledge,
    |                         concerns, works, decision_policy; imitation
    |                         (options, consider, work a year, learn)
    +-- Household             the founder's; storage delegates to the live
    |                         simulation state; idles (decisions arrive as
    |                         commands)
    +-- RecordedActor         storage is one persistent ActorRecord
        +-- Government       a country's state
        +-- Firm             an independent business

`Actor` leaves storage and valuation to subclasses: `money`, `workforce`,
`knowledge`, `concerns`, `works` and `imitation_worth`. New actor kinds are
added by subclassing and registering in `ACTOR_CLASSES`
(`actors/registry.py`); nothing else enumerates kinds.

## Policy

Every decision is a `Decision` (kind, options, budget) handed to the actor's
`decision_policy`, which returns the chosen options.

- `ValuePolicy`: best net value first within the budget, nothing at a loss.
- `CallbackPolicy(function)`: a human player or a mod names the subjects; names
  not on offer are ignored.
- `IdlePolicy`: never acts.
- `register_policy(name, factory)` makes a policy nameable; an actor record
  stores only the name, so a saved actor gets its policy back on load.

## Value of an invention

An invention has gains per dimension: the node's declared `gains` mapping if
it has one (a mod can add it to any node), otherwise one unit per trait it
carries (`actors/values.py`). An actor turns gains into worth with its own
weights:

- Government: the civilisation's trait weights (`state_trait_weights`, the
  same table that drives state interest), times revenue it raises, times a
  worth-per-gain share. A negative weight means the state does not want it.
- Firm: the margin it expects from a concern it can enter, over a payback
  horizon. It ignores everything that is not such a concern.

Worth is multiplied by exposure: visible use (a running concern) versus
kept out of public use, and distance from the founder's base for an actor
with a location.

## Cost and difficulty of copying

`actors/imitation.py`. The copy covers the unknown prerequisite chain that
the founder has demonstrated (knowledge distance is real work, and a chain
with an undemonstrated gap cannot be copied). Hours per trade, money and
calendar years derive from the node's labour and cost, scaled by a copying
share; trades the actor does not already staff cost a hiring premium. Each
year the actor pays wages and money for the share of the work done; a short
purse slows the work, nothing is forgiven. On completion a keyed random draw
(independent of the world's own stream) decides success from the risk of each
step. Failure costs what was spent and is counted.

## Firms

`ActorRegistry.consider_entry`: a founder concern that has run at a profit
for long enough is proven. An entrant is founded if the profit share it
expects, over the horizon and weighted by copy success, exceeds its cost, and
the society's pooled capital can fund the stake. The firm then copies the
concern through the ordinary imitation path, opens it, shares its takings with
every other operator, and closes after consecutive losing years.

## Government

Created per civilisation by `advance_actors`. It receives a share of the
revenue derived from the working population's labour value, the civilisation's
tax share and state capacity, and spends it on copies its policy chooses.

## State and persistence

`SimulationState.actors` holds an `ActorsState` of `ActorRecord`s, saved and
loaded by the automatic dataclass mechanism. Actor objects are rebuilt from
records whenever the state object is replaced. Provisional numbers live in
`actors/tuning.py` and are declared heuristics
(`python3 sim/constants.py --burndown`).

## Not yet built

See the status line of Complaint 107.
