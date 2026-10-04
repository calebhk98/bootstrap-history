# Multiplayer: players, countries, traders and strata as actors

Every party the founder deals with is an actor in `ActorRegistry`. That includes other players, the
home state, foreign states, competitor firms, traders and the bodies of people (strata). The engine
sees only the registry, through `api.py` and its adapters (`sim/engine/agents_port*.py`,
`sim/engine/society_actors.py`). One actor or fifty, nothing outside this package changes.

Research behind the choices: `RESEARCH.md`.

## The cast: who is in a game

`ActorsState.cast` is the game's roster: one `CastEntry` per starting actor. `ActorsState.countries`
holds one `CountryProfile` per country. Both are seeded once, at the first actor year, and saved
with the game. Each save therefore keeps the world it began with: a Rome start and a Han start get
different casts, and nothing about either is in code.

Where the seed comes from (engine adapter `agents_port_cast.py`):

1. The civilisation the game was started with. It becomes `home_country` and gets the home
   government.
2. The foreign economies enabled for the start year (`data/world/foreign_economies.json`). Each one
   becomes a country with a profile built from its own civilisation file and a foreign government.
3. An optional `"cast"` key in the civilisation dict, which adds further countries, players and
   strata. Mods already patch civilisation files, so a mod adds actors without new loader code.

## Countries and their trees

Every record carries `country` (None means the home country). The registry hands an actor of another
country a scoped world (`register_world_scope`). That world answers country questions from the
profile: population, capacity, the baseline tree (the country's `starting_techs`) and its own
government. Shared questions such as the year, the market and randomness pass straight through to
the shared world. A firm in a country therefore starts from that country's techniques, as does a
trader or a player who belongs to it.

## Kinds and spawners are registered, never enumerated

- `register_actor_kind(kind, cls)` lets a mod add a kind of actor.
- `register_spawner(name, fn)` adds a rule that founds actors after the year's turns. Firm entry,
  interest groups and trader entry are spawners.
- No code names a civilisation, a node or a particular actor.

## Who decides

NPCs use `ValuePolicy`: best net value first, within budget, never at a loss. A human or an LLM
player has `controller` set and queues commands in `record.orders`. The player's turn runs them in
order and writes each result to `record.journal`. A command is plain data, so a save carries
whatever is pending and a replay reproduces it.

## The kinds

| Kind | Module | Created by | Decides with |
|---|---|---|---|
| `government` | `government.py` | cast (home country) | budget, levy, `ValuePolicy` copies |
| `foreign_government` | `government_foreign.py` | cast (each partner) | revenue from its profile, army and officials, copies under fog |
| `player` | `player.py`, `player_commands.py` | cast `"actors"` (a join command is Complaint 401) | queued orders; `controller == "ai"` adds a simple research-and-open rule |
| `firm` | `firm.py`, `concern_ops.py` | spawner `firm_entry` after any player's proven concern | entry value, exit on losses |
| `trader` | `trader.py`, `trader_entry.py` | spawner `trader_entry` when a route's gap pays | best margin within capital, sized to a share of depth |
| `stratum` | `stratum.py`, `stratum_year.py`, `strata_seed.py` | spawner `strata` for every country | income against needs in tiers; growth, schooling and mobility follow |
| `interest_group` | `group.py` | spawner `interest_groups` | presses the state |

A stratum's data says what its people earn by. `trade` gives wages, `property_share` gives a share
of output, `bonded` means kept by an `owner` stratum, and `own_plot` means it falls back on its own
land when wages fall short. `rises_to` and `falls_to` name where its members move.

## One goods market for now

There is one goods market: the home society's. A firm or player of a foreign country counts as a rival
of home operators, and what its concerns make is sold there. A trader's sale abroad moves only money
(Complaint 405). Markets per country come with the agent economy's partners becoming economies
(Complaint 382, step 4).

## Money

Every payment between actors goes through `ledger.transfer`. Money enters or leaves only at a named
edge (for example, a foreign country's revenue from people the simulation does not model actor by
actor). Tests check that the sum of purses is conserved across a year apart from those edges.

## What lives elsewhere

- **Goods-level clearing, cohorts and merchants of the agent economy:** `sim/economy/`.
- **The founder's projects and household:** the engine (Complaint 382).

Open problems are in Complaints 401 (no protocol command reaches a second player), 402 (the
founder is not a `Player`), 403 (strata income figures disagree), 404 (cast data undocumented, no
slaves declared) and 405 (traders beside the other merchant models).

The actors here decide and own. Where the agent economy already models the same people or trade,
the adapter reads it rather than this package modelling it twice. Open complaints track where the
two still overlap.
