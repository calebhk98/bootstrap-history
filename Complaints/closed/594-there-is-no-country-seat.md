# There is no country seat: a seat is always a household

**Status:** done - a country seat joins, holds that country's government, has no founder or household, and hands over

Part of Complaint 481 (A player cannot play as a country).

Depends on 593 (a country-scoped government to hold). Blocks 595.

**What is wrong.** A seat is "a household, what it has built and learned, its goal and its founder" (`sim/PROTOCOL.md`, "SEATS"). `join` takes an optional `country`, but the seat is still a household living there. The Rome start tells the player "You are one household, not the Roman state" (`data/civilizations/rome_100ad.json`, `what_this_models`). The group fakes a country player by treating the founder as the state.

**Evidence.** `sim/PROTOCOL.md` SEATS; `data/civilizations/rome_100ad.json` `what_this_models`.

**Why it matters.** CLAUDE.md section 2 says other countries will be players and every mechanism must be usable by any actor.

**What it would take.** A `country` seat kind whose holder is a government actor, chosen at `join`; a household seat is unchanged. Update `sim/PROTOCOL.md` SEATS.

**Test.** A test joins a country seat and reads the reply fields: the seat's holder is that country's government, it has no founder household, and the year runs; a household seat's reply is unchanged.

## What was done

- `SeatState` has a `kind` (`household` default, `country`) and a `holder` (the government actor id of a country seat); `sim/engine/state_seat.py`.
  `join` takes `seat_kind: "country"` and an optional `country` (default the game's own); `join_seat` sets the holder from the country's
  `Government` (`sim/engine/seat_run.py`, `sim/ui/proto/dispatch_seats.py`). The reply carries `holder`, `founder: null`, `household: null`.
- A country seat has no founder (`founder` is None) and only an empty placeholder household that the engine's aliases need. It is not among
  `playing_seats`, so the household phases of the year skip it, and it neither ends nor holds open the game (`run_is_over` reads household seats).
  The government acts with the actors' year as before.
- Commands that need a household are refused for a country seat with `cause` `country_seat_has_no_household`; `step` from a country seat runs
  the year as the first playing household seat (`sim/ui/proto/seat_address.py`).
- Handover uses the same path: kind and holder are moved fields; a country seat passes only to a country seat (`replacement_wrong_kind`).
- `sim/PROTOCOL.md` SEATS updated. The Rome `what_this_models` text is still right for the default household seat and is unchanged.
- A household seat's join reply and rows are unchanged.

**Left:** the state's levers are 595. Two country seats may name one country (so a replacement can join before a handover) and share its government until one hands over.

**Test:** `sim/tests/test_country_seat.py` (slow: the holder is a government actor the cast seeds, so the join path needs a whole game).
