# There is no country seat: a seat is always a household

**Status:** open

Part of Complaint 481 (A player cannot play as a country).

Depends on 593 (a country-scoped government to hold). Blocks 595.

**What is wrong.** A seat is "a household, what it has built and learned, its goal and its founder" (`sim/PROTOCOL.md`, "SEATS"). `join` takes an optional `country`, but the seat is still a household living there. The Rome start tells the player "You are one household, not the Roman state" (`data/civilizations/rome_100ad.json`, `what_this_models`). The group fakes a country player by treating the founder as the state.

**Evidence.** `sim/PROTOCOL.md` SEATS; `data/civilizations/rome_100ad.json` `what_this_models`. Also stale: `sim/agents/MULTIPLAYER.md` still lists Complaints 401 to 405 as open; all are closed.

**Why it matters.** CLAUDE.md section 2 says other countries will be players and every mechanism must be usable by any actor.

**What it would take.** A `country` seat kind whose holder is a government actor, chosen at `join`; a household seat is unchanged. Update `sim/PROTOCOL.md` SEATS and correct the closed list in `sim/agents/MULTIPLAYER.md`.

**Test.** A test joins a country seat and reads the reply fields: the seat's holder is that country's government, it has no founder household, and the year runs; a household seat's reply is unchanged.
