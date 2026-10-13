# A player cannot play as a country: a seat is a household and every state is an NPC with no commands

**Status:** open

An alt-history group wants to run worlds where each player is a country (several at once), and fakes it
today by treating the founder as the state. The engine cannot host that:

- **A seat is a household.** `sim/PROTOCOL.md` ("SEATS"): a seat is "a household, what it has built and
  learned, its goal and its founder". `join` takes an optional `country`, but the seat is still a household
  living in that country. The Rome start says so to the player: "You are one household, not the Roman
  state" (`data/civilizations/rome_100ad.json`, `what_this_models`).
- **The state takes no orders.** The command registry (`grep -rhoE '@command\("[a-z_]+"' sim/ui/proto | sort -u`)
  has no command to set a tax form or rate, a budget line, an army size, a reserve floor, a monopoly, a
  subsidy, a war or a treaty. `policy` switches a seat's automatic actions only. The home `Government`
  (`sim/agents/government.py`) and every `ForeignGovernment` decide by their own rules.
- **A seat cannot be handed over.** A seat ends when its founder dies (`sim/engine/seat_run.py`) and is
  dropped from the year (`sim/engine/year_run.py`); nothing passes its knowledge, holdings or notes to
  another player. The group asked for this so a replacement player inherits what the leaver knew.
- **Mods cannot fill the gap without base-game work.** Mod code (`sim/engine/mod_code.py`) can register
  commands, actor kinds, policies and spawners, and a handler receives the whole `sim`. But the state it
  would need to drive is missing or frozen in the base game: tile ownership is fixed at setup
  (`sim/economy/setup.py` `country_of`), other countries have no demography (Complaint 482), there is no
  army object (485), and the year has no hook between phases for a conflict or politics step. A mod would
  have to reimplement those core systems against the internal `Sim` surface, which is what the group's
  reviewer reported.
- **Stale document.** `sim/agents/MULTIPLAYER.md` still lists Complaints 401 to 405 as open; all are closed.

Why it matters: CLAUDE.md section 2 says "every mechanism the founder uses must be usable by any actor"
and that other countries will be players. Every other gap filed from the same review (482 to 493) is a
piece of this one.

What it would take: a `country` seat kind whose holder is a government actor; protocol commands that set
that government's policy levers (revenue forms and rates, budget lines, army and navy targets, works,
subsidies and mandates); the home `Government` model made country-scoped so any country can be one
(482); a seat handover command; and the mod hooks in Complaints 494 to 496 (a phase registry for the year, declared per-tile and
per-actor stores, and stable effect operations), with the systems in 482 to 493 built on those hooks so
that a mod could have written them. Review that led here:
`Complaints/reports/alt-history-requirements-review.md`.
