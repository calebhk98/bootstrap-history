# Malformed command arguments are accepted silently

**Status:** partly - unknown fields are refused with `unknown_field` and `help` takes `topic`, but the check is global: a field any command reads is accepted by every command (`id` on `policy` passes); per-command validation against each command's declared arguments is open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`):

- `{"cmd":"policy","auto_hire":"on"}` replied `ok: true` and changed nothing; the accepted form is `"set": {...}`.
- `{"cmd":"help","command":"sell"}` returned the front page instead of the help for `sell`.

Why it matters: an agent player learns the protocol from replies; an `ok` for a request that did nothing teaches it
the wrong form, and it then believes a policy is on that is off.

What it would take: every command validates its fields against its declared arguments (the command registry already
declares usage, `sim/ui/proto`), and an unknown field is a refusal with `cause: "unknown_field"` naming it. Test: the
two requests above are refused with that cause.

## Resolution

Before dispatch, `sim/ui/proto/field_check.py` refuses a field that no handler reads and no usage form declares, with cause `unknown_field`, the field, and the fields the command takes (`accepted_fields`). The known fields are found by scanning the handlers, not listed. `help` documents its `topic` field in its usage. Test: `sim/tests/test_unknown_field.py`.
