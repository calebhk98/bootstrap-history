# Behaviour tests assert on player-facing wording

**Status:** closed - `python3 -m sim.tests --text-checks` lists no behaviour check that reads text

Several tests that check what the model does read it from the text a screen prints (for example
`round8g_display`'s `path` checks and `interface_honesty`'s EARNS/YR checks, fixed in the
`fix-red-slow-ui-topics` merge). When the wording or the rounding changes, the check fails although the model
did not change; when the model changes, a reworded message can hide it. 362 (all player text moves to `sim/ui/`)
makes this worse if it is not fixed first.

Rule (owner, 2026-10-14): a test of model behaviour asserts on structured values (the engine's numbers or the
JSON reply's fields). Only a test whose subject is presentation (units, wording, rounding, layout) asserts on
text. The rule is in CLAUDE.md section 6.

## Resolution

- **The list.** `python3 -m sim.tests --text-checks` reads the test sources and prints the checks that match on
  reply, log or screen text and are not presentation; it must print none. `--all` also prints the presentation
  ones with the basis for calling them that (`marker`, `renderer`, `topic`, `name`), and `--conditions` prints each
  check's condition. It is a heuristic over the syntax tree (`sim/tests/text_checks.py` says what it recognises);
  a check that reads text through a helper it does not know is not counted.
- **Presentation stays on text.** A check whose subject is wording says so with a `# presentation: <reason>`
  comment; a stored value or an enumerated field the heuristic misreads as wording carries `# not text: <reason>`.
  The `name` and `topic` bases are guesses from words in the check's or the topic's name; audit them with
  `--all` when a topic is touched.
- **Behaviour reads values.** Where the fact existed only as prose, the reply (or the engine object behind it)
  now carries it, and the text is built beside it (`sim/refusal.py`):
  a refusal's `cause` (and `choices`, `facts`), a log line's `kind` and `facts` (replies show them as
  `event_kind` and `facts`), `blocked_kind`/`blocked_cause` on a refused `start` and `cause` on each start
  blocker, `waiting_on_kind`, `stopped_kind`, `why_kind`, `did_nothing_kind`, an automation row's `reason_kind`,
  the ordered `remedies` in room and staff advice, a hazard relief entry's `source`, a sector's `forms` and
  `facts`. `sim/PROTOCOL.md` lists the replies.

## Known gaps

- `sim/ui/proto/dispatch.py` still reads the founder's age out of the death line's text, and the step's
  stop-marker and failure-line predicates (`_STEP_STOP_MARKERS`, `_is_failure_line`, `event_tier`) still match on
  wording; they could read a log line's `kind` now that it exists.
- Log lines lose their `kind` when a game is saved and loaded; a reply built from a loaded log has the text only.
- `closure_reasons` and `labour_productivity` are red on the branch this was cut from (the set-up that opens the
  supervised concern fails), so their converted checks there were checked by hand, not by the topic.
