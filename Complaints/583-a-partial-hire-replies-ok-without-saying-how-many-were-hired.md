# A partial hire replies ok without saying how many were hired

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-to-221.md`, 102 AD). `hire artisan 4` returned `ok` having hired one; `hire labourer 2`
hired labourers whom the help text implied would supervise as craftsmen, and `fire` refunded nothing.

What it would take: a hire that fills fewer than asked replies with the number hired, the number asked and the
`cause` of the shortfall (no one left, wage above what you set); the help text's account of which trades count as
craft reads the same trade data the supervision check uses; tests for both.
