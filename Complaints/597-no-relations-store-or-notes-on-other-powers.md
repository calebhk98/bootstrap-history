# There is no relations store: no place to record a treaty, trust or a player's view of another power

**Status:** open

Part of Complaint 487 (No diplomacy).

Seat-to-country comes from `core_seats.py` and `agents_port_seats.py`. Blocks 598.

**What is wrong.** Nothing keys state or a note to a pair of actors. The `note` command keeps a seat's free text by year or attached to a project; nothing keys a note to another country, and a note dies with its seat.

**Evidence.** `sim/engine/living_stock_smuggling.py` notes the diplomatic memory "the model does not yet have"; `sim/ui/proto/dispatch_notes.py`.

**Why it matters.** The group wants relations that change what each power will do, and at least a place to record a player's view of another power. A note store is the cheap first step.

**What it would take.** Declare an actor-pair `relations` store in `data/world/stores.json` (treaty terms, tariff, embargo, trust, note); `relations` and `set_relation` commands where a seat sets only its own country's side; notes keyed to a country, not a seat, so they survive it (`dispatch_notes.py`; see 481 and 596).

**Test.** A test sets a note and a treaty term for a pair, saves and loads, and reads them back; a seat cannot set the other country's side (refusal `cause`); the note survives the seat.
