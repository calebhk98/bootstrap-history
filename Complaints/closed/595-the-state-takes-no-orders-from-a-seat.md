# The state takes no orders: no protocol command sets a tax form or rate, a budget line, an army size, a reserve floor, a monopoly or a subsidy

**Status:** done - the `lever` and `levers` commands set a country seat's own government's levers; rates carry no consequences until 625 and 626

Part of Complaint 481 (A player cannot play as a country).

Depends on 594 and 593. Tax rates become a real choice only when 626 lands; until then a lever accepts any rate the file allows. War is 485 and treaties are 597 and 598.

**What is wrong.** The command registry has no command to set a state's policy. `policy` switches a seat's automatic actions only. The home `Government` and every foreign government decide by their own rules.

**Evidence.** `grep -rhoE '@command\("[a-z_]+"' sim/ui/proto | sort -u`; `sim/agents/government.py`.

**Why it matters.** A country player with no levers cannot play.

**What it would take.** Protocol commands (registered under `sim/ui/proto`) that set the seat's own government's levers: revenue forms and rates, budget lines, army and navy targets, works, subsidies, mandates, reserve floor, monopolies. A seat may set only its own country's levers; anything else is a refusal with a `cause` (`sim/refusal.py`).

**Test.** Tests read structured values: a lever command changes the government's field and the next year's ledger; setting another country's lever is refused with a `cause`.

## What was done

- `lever` and `levers` (`sim/ui/proto/dispatch_levers.py`, documented in `sim/PROTOCOL.md`) set revenue rates (or start a form on a modelled base),
  budget-line shares, army and navy targets, works stocks, the reserve held before a surplus is spent, monopolies, subsidies and mandates.
  The rules are plain functions in `sim/agents/government_levers.py` (`set_lever` answers the change or a `Refusal`); the record holds them in
  `ActorRecord.levers`, and monopolies use the existing `state_monopolies`.
- The Government reads them: `budget.standing_lines` (army target, line shares, navy, subsidy and mandate lines), `state_works.wanted_of`,
  `Government.build_works` (reserve), and `revenue_forms` of both the home and the country world.
- A subsidy is a money line handed to the good's producers; a mandate is a line buying tonnes of a good. Neither has a deeper mechanism yet.
- A household seat is refused (`household_seat_has_no_government`), another country (`not_your_country`), an unknown lever or name
  (`unknown_lever`, `unknown_name`, `unknown_basis`), a bad value (`value_not_number`, `value_out_of_range`, `value_not_boolean`).
- Tests: `sim/tests/test_government_levers.py` (quick; rules on built Government records, read by the budget and revenue functions) and
  `sim/tests/test_country_seat_levers.py` (slow; the protocol reply).

**Left:** a rate is any share of its base (0 to 1) until 625 and 626 give rates consequences; a line share can only cut a derived line
(army, navy and works targets enlarge). Mandates and subsidies change nothing beyond the state's own demand. A partner country's seat uses the same
path but only the home country is covered by the protocol test.
