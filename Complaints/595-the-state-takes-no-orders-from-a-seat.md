# The state takes no orders: no protocol command sets a tax form or rate, a budget line, an army size, a reserve floor, a monopoly or a subsidy

**Status:** open

Part of Complaint 481 (A player cannot play as a country).

Depends on 594 and 593. Tax rates become a real choice only when 626 lands; until then a lever accepts any rate the file allows. War is 485 and treaties are 597 and 598.

**What is wrong.** The command registry has no command to set a state's policy. `policy` switches a seat's automatic actions only. The home `Government` and every foreign government decide by their own rules.

**Evidence.** `grep -rhoE '@command\("[a-z_]+"' sim/ui/proto | sort -u`; `sim/agents/government.py`.

**Why it matters.** A country player with no levers cannot play.

**What it would take.** Protocol commands (registered under `sim/ui/proto`) that set the seat's own government's levers: revenue forms and rates, budget lines, army and navy targets, works, subsidies, mandates, reserve floor, monopolies. A seat may set only its own country's levers; anything else is a refusal with a `cause` (`sim/refusal.py`).

**Test.** Tests read structured values: a lever command changes the government's field and the next year's ledger; setting another country's lever is refused with a `cause`.
