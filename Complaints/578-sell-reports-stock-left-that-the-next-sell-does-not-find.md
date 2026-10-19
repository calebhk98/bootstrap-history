# Sell reports stock left that the next sell does not find

**Status:** open

Found by an agent playtest (`Complaints/reports/playtest-rome-seed11-agent-legitimate-log.md`, 111 to 125 AD). A `sell` reply said over a thousand tonnes were left; the next
`sell` found a small fraction of that. A `sell` of more than is held errors out instead of refusing with a `cause`.

What it would take: the reply's stock left reads the same holding the next sale draws on (one function), and selling
more than is held is a refusal with `cause: "not_enough_held"` and the quantity held; tests for both.
