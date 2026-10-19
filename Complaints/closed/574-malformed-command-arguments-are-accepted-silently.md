# Malformed command arguments are accepted silently

**Status:** closed - each command refuses a field its own handler and declared usage do not take, with `unknown_field`

Found by an agent playtest (`Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`):

- `{"cmd":"policy","auto_hire":"on"}` replied `ok: true` and changed nothing; the accepted form is `"set": {...}`.
- `{"cmd":"help","command":"sell"}` returned the front page instead of the help for `sell`.

Why it matters: an agent player learns the protocol from replies; an `ok` for a request that did nothing teaches it
the wrong form, and it then believes a policy is on that is off.

What it would take: every command validates its fields against its declared arguments (the command registry already
declares usage, `sim/ui/proto`), and an unknown field is a refusal with `cause: "unknown_field"` naming it. Test: the
two requests above are refused with that cause.

## Resolution

Before dispatch, `sim/ui/proto/field_check.py` refuses a field the addressed command does not take, with cause `unknown_field`, the field, and the fields that command takes (`accepted_fields`). A command's fields are found, not listed: what its handler reads off the command, following the command into the helpers and handler tables the handler references, plus the fields its declared JSON usage forms carry. Every command also takes the reply wrapper's `compact` and the typed parser's `json` switch. A mod's handler and a handler with no source of its own are not checked. `{"cmd":"policy","id":"x"}` is refused; `help` documents its `topic` field in its usage. Tests: `sim/tests/test_unknown_field.py` and `sim/tests/test_unknown_field_per_command.py`, which also scans every command written out in the tests. Three tests that sent a field their command ignores (`step n`, `start node`, a macro's `quit text`) now send the real one.
