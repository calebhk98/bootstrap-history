# No command reaches a second player: the protocol and the CLI address only the founder

**Status:** closed - folded into 382

A second player now exists as an actor: `sim/agents/player.py` (`Player`, kind `"player"`). Its
commands are plain records queued in `record.orders`, and each result is written to `record.journal`
(`sim/agents/player_commands.py`). The commands are research, open, close and transfer, and
`register_command` lets a mod add more. Nothing outside `sim/agents/` lets a human or an LLM put an
order there or read the journal back.

- `sim/simulator.py`, `sim/ui/` and `sim/PROTOCOL.md` take every command as the founder's.
- No session or player id is passed with a command.

What it would take:
- A player id on the agent and JSON protocol, for example `--player player:2`.
- Commands for that id that append to `record.orders` through the actors api, never by editing the
  record directly.
- A screen or JSON block that renders the player's purse, knowledge, concerns and journal.
- A way to add a player to a new game, for example a `"cast"` entry or a `join` command that creates
  a `"player"` record.

Turn order: today every actor acts in id order inside one yearly turn. Simultaneous resolution
(WEGO) is noted in `sim/agents/RESEARCH.md`.
