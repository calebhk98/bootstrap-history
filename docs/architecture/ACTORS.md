# Actors

Who can own money, staff, know-how and works, and decide. Code:
`sim/agents/`. Tests: `sim/tests/test_actors.py`. Tracking:
`Complaints/closed/103-add-independent-firms-imitation-entrepreneurship.md`.

## Class layout

    Actor                     shared surface: money, workforce, knowledge,
    |                         concerns, works, decision_policy; imitation
    |                         (options, consider, work a year, learn)
    +-- RecordedActor         storage is one persistent ActorRecord
        +-- Government       a country's state; its concerns are plain parts
        +-- Firm             an independent business; an expansion part
        +-- Player, Stratum, InterestGroup, Trader, DeclaredKind,
            Church, Academy  the other shipped kinds (`sim/agents/shipped.py`)

    HouseholdParty            not an Actor: a seat (the founder's or another
                              player's) seen as a party to an exchange; it
                              holds no state, and maps the names an exchange
                              asks for onto the modules that own the seat's
                              purse, staff, know-how and plants
                              (`household_party.py`)

`Actor` leaves storage and valuation to subclasses: `money`, `workforce`,
`knowledge`, `concerns`, `works` and `imitation_worth`. Kinds are not listed
in one table: the actors module owns the `actor_kinds` extension point
(`sim/actors/module_spec.py`), the game's own kinds come from `shipped_kinds`
in `sim/agents/shipped.py`, a mod can add `DeclaredKind` declarations, and
`ActorRegistry` builds an actor from its record's `kind` through the combined
`ActorExtensions` (`sim/agents/extensions.py`). A record whose kind is not
provided is refused.

A `Government` holds its concerns as plain part objects (corvee, credit
record, fiscal, coinage, enterprises, granary, markets, stores, surplus),
each addressed as `government.<part>.<method>`; a `Firm` holds an `Expansion`
part. See the class docstrings in `sim/agents/government.py` and
`sim/agents/firm.py`. Households inside a stratum, each with its own wealth,
are in `sim/agents/household_wealth.py`.

## Policy

Every decision is a `Decision` (kind, options, budget) handed to the actor's
`decision_policy`, which returns the chosen options.

- `ValuePolicy`: best net value first within the budget, nothing at a loss.
- `CallbackPolicy(function)`: a human player or a mod names the subjects; names
  not on offer are ignored.
- `IdlePolicy`: never acts.
- A policy is made nameable by providing it to the actors module's `actor_policies` point (`api.policy`); an actor record
  stores only the name, so a saved actor gets its policy back on load.

## Value of an invention

An invention has gains per dimension: the node's declared `gains` mapping if
it has one (a mod can add it to any node), otherwise one unit per trait it
carries (`sim/agents/values.py`). An actor turns gains into worth with its own
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

`sim/agents/imitation.py`. The copy covers the unknown prerequisite chain that
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

Created per civilisation by the actors module's `advance_actors` command (`sim/actors/year.py`). It receives a share of the
revenue derived from the working population's labour value, the civilisation's
tax share and state capacity, plus whatever the state takes from the founder,
and spends it on copies its policy chooses.

## Money between actors

`sim/agents/ledger.py`. Every change of an actor's purse goes through `credit` and
`debit` with a purpose; `transfer(payer, payee, amount, purpose)` is the one
way a loss becomes a gain. A recorded actor keeps `income` and `outlays` by
purpose, so its purse equals its opening money plus income less outlays. The
founder's household pays the state through `pay_state` (`sim/polity/transfers.py`), and the government
of the founder's civilisation receives requisition, the pressed office,
military supply and confiscation. Each
purpose's share of a run's income and outlays is in the actor ledger.

## State and persistence

The actors module's world slot holds an `ActorsState` of `ActorRecord`s (`SimulationState.actors` reads it), saved and
loaded by the automatic dataclass mechanism. Actor objects are rebuilt from
records whenever the state object is replaced. Provisional numbers live in
`sim/agents/tuning.py` and are declared heuristics
(`python3 sim/constants.py --burndown`).

## Not yet built

See the status line of Complaint 103.
