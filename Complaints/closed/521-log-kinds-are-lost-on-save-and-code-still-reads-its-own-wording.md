# A log line's kind is lost on save and load, and some code still reads its own wording

**Status:** closed

Found closing 515. Step events and log entries now carry `event_kind` and `facts` (`sim/refusal.py`, `LogLine`),
but the household log is saved as text, so after a save and load (every command with `--session`, CLAUDE.md 4.6)
the kind and facts are gone; a player on `--session` and a test in one process see different replies. And some
engine code still decides by matching its own sentences: `sim/ui/proto/dispatch.py` parses the founder's age out
of the death line, and the step stop-marker, failure-line and severity predicates match on wording where they
could read `kind`.

What it would take: save log entries as structured records (text, kind, facts) and render them on read; switch the
predicates to `kind`; carry the age as a field. Test: a reply's events have the same kinds and facts after a save
and load as before (extend the save round-trip topic), and no engine or dispatch predicate matches on a log line's
text (`python3 -m sim.tests --text-checks` covers tests; this needs a matching check over `sim/`).

## Resolution

- A `Refusal` or `LogLine` is saved as a record (`__log_line__` or `__refusal__` holding the code, then `text`,
  `choices` and `facts` when present) and rebuilt on load (`sim/refusal.py` `as_record`/`from_record`, called from
  `serialize_state` and `_deserialize_typed`). No older save loads (4.6).
- Which kinds are bad news, stop a step, are notable or carry a severity tier is the table in
  `sim/ui/proto/event_kinds.py`; severity, `log failures`, the step stop, `changes`, the wave summary, the step
  alerts and problems read it. The founder's age is the `aged` fact of the `founder_dies` line, and lapsed hedges
  are the `lapsed_hedges` fact.
- `python3 -m sim.tests --text-decisions` (topic `text_decisions`) lists code under `sim/` that decides on a log
  line's or refusal's text; it finds none. Remaining wording reads outside its scope: `sim/engine/fuzzy_estimates.py`
  masks figures in a `why` reply's sentences.
