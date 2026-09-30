# `ventures` hides most shut concerns and cannot be paged

**Status:** closed - `ventures` takes offset/limit (default 20 rows, "ventures offset:N" hint); shut_concerns_in_all reports the total

At 534 AD `ventures` listed 12 "YOU KNOW HOW, AND HAVE NOT OPENED" rows then "...and 117 more"; `state` said 142. `help ventures` shows no options; `ventures all`, `ventures offset:12`, `ventures limit:200`, `ventures full` all print the same rows; `ventures json` is capped at 20 (`and_more_you_could_open`). `stuck` names only "the best you could open".

Workaround I used: page `log find:completed limit:100 offset:N` (393 completions = 4 calls), extract the `open <id>` hints, subtract the complete running list from `ventures json`, and send one `open` per remaining id. It opened 79 concerns `ventures` never listed; it is five invocations and a text-extraction step for "which of my businesses are shut?".

What it would take: `offset`/`limit` on `ventures` as on `available` and `log` (or a `ventures shut` list).

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
