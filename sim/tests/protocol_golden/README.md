# Protocol golden transcripts

What the `agent` protocol answered on the code they were recorded from. One file per script, each
`{"script", "arguments", "transcript": [{"cmd", "reply"}, ...]}`. The scripts are in
`sim/tests/protocol_golden_scripts.py`; `sim/tests/test_protocol_golden.py` replays them in-process
(`sim/tests/cli_in_process.py`) and names the first differing command and key.

Re-record, only when a reply is meant to change: `python3 -m sim.tests.test_protocol_golden --record`.
Run: `python3 -m sim.tests --only protocol_golden --topic-seconds 240`.

Replies are normalised by `sim/tests/protocol_golden_support.py` (`normalise`): numbers, booleans and
null stay as they are; a string that looks like an id (lower-case letters, digits, `_ : . -`, at most 48
characters) stays; `cause`, `event_kind`, `kind` and `cmd` stay whatever they hold; every other string is
replaced by `~prose~`. `facts` are numbers and ids, so they stay. The games run with the suite's settings
(short hidden spin-up, default seed 1, dice off), so a fixture is not the same as a game run outside the suite.

| Script | Game | Covers |
|---|---|---|
| `rome_founder` | rome_100ad, seed 7, one invocation | the overview and money reads, market and materials, available/why/path, help pages, start/stop/priority/pursue/exclude/include/programme, hire/train/commission/fire/labour, bounty/pay/buy/sell/found/quote, notes, step over several years, `save` then `load` inside one run |
| `han_two_seats_fog` | han_china_100ad, seed 3, `--fog` | second seat via `join` and `"as":"second"`, per-seat reads and starts, share offers between seats, fog refusals (`never_heard_of`), relations, handover refusals, country-only command refusals, stepping, `finish` |
| `norse_session_round_trips` | norse_900ad, seed 5, `--session` | seven invocations, each loading the save the last wrote and writing it after every command: reads, start, hire refusal, step, bounty, score, `finish` |

## Replies with no structured field to compare

Their refusals (`{"ok": false, "error": ...}`) carry no `cause`, so the fixture holds only `ok` and a
placeholder for them. When one of these gains a `cause`, add it to the reply.

`bounty` (no id), `bribe` (no amount), `changes` (before any year), `join` (a seat that exists), `pay` (no
debt), `quote` (open before the knowledge exists), `start` (unknown id, and a node a precondition forbids),
`stop` (not active), and an unknown command word.

## Commands in the registry that no script reaches

`accept`, `decline`, `offer` (need a second seat holding something to trade); `answer`, `withdraw` (need a
state demand); `build_way`, `prospect`, `settle` (need the matching knowledge, which no cheap opening
reaches); `close` (needs a mine); `open`, `mothball`, `restore` (need a finished concern that has been
opened); `work`; `options` (its reply carries the machine's save directory); `quit`; `levers`.

Country seats (`join` with `seat_kind` `country`) are not exercised either: `levers`, `lever` and `relations`
sent `"as"` such a seat answer `internal error handling that command: AttributeError: 'NoneType' object has
no attribute 'dead_reason'` on the code these were recorded from (`seats` and `join` work). That is a bug, not
a behaviour to keep, so no fixture records it. Once it is fixed, add a country seat to
`han_two_seats_fog`.
