# A partial hire replies ok without saying how many were hired

**Status:** closed - a short hire replies with hired, asked and a cause; the craft help reads the supervision check trade data

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, 102 AD). `hire artisan 4` returned `ok` having hired one; `hire labourer 2`
hired labourers whom the help text implied would supervise as craftsmen, and `fire` refunded nothing.

What it would take: a hire that fills fewer than asked replies with the number hired, the number asked and the
`cause` of the shortfall (no one left, wage above what you set); the help text's account of which trades count as
craft reads the same trade data the supervision check uses; tests for both.

## Resolution

`hire` replies `hired` (the number found), `trade`, `asked` and, when fewer were found, `cause` `search_found_fewer` (the labour market matching found fewer than asked). The `ventures` help names craft and non-craft trades from `craft_trades_report`, which uses `is_craft_trade`, the test the supervision count uses; the prose list is gone. Tests: `sim/tests/test_complaint_583_partial_hire_and_craft_help.py`.
