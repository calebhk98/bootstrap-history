# Playtest brief

You are playing a game. Read this whole file before your first command.

## The one hard rule

**You may only interact with the game through the JSON protocol.**

```bash
python3 rome/sim/simulator.py agent --civ <CIV> [--kit <KIT>] [--seed N]
```

It reads one JSON command per line on stdin and writes one JSON object per line
on stdout. You drive it however you like: by hand, or by writing your own script
that pipes commands into it and reads the replies.

**Forbidden**, because the whole point is to find out whether a player can do
this without them:

- `simulator.py run`, `compare`, `sensitivity`, `sweep`, `path` (the CLI one),
  `costs`, `why` (the CLI one), or `treetool.py` in any form
- importing `simulator` as a module and calling `load_strategy`, `Sim`, or
  anything else directly
- reading `rome/data/strategies/`, or any file that encodes the optimizer's
  chosen ordering
- reading the tech tree JSON to plan. You may read it ONLY to check a
  specific claim after the game has told you something you doubt, and if you do,
  say so in your report

Reading `rome/knowledge/` is allowed and encouraged. It is the in-world guide;
a real player would have it. Reading `ROME_BOOTSTRAP.md` is allowed.

`path`, `why` and `available` ARE protocol commands and you should use them
freely. The ban is on the command-line versions and the optimizer, not on
information the game itself offers you.

## The protocol

```
{"cmd":"state"}                              current situation
{"cmd":"available"}                          everything you could start now
{"cmd":"why","id":"zinc_metal"}              full explanation of one node
{"cmd":"path","id":"point_contact_transistor"}   what a node still needs
{"cmd":"start","id":"..."}                   begin a project
{"cmd":"stop","id":"..."}                    abandon one
{"cmd":"bounty","id":"..."}                  pay someone else to solve it
{"cmd":"buy","what":"forest|mine|slaves|manumit","n":100}
{"cmd":"step","years":5}                     advance time
{"cmd":"quit"}
```

Errors come back as `{"ok":false,"error":"..."}` and the message tells you what
to do instead.

## The premise

You are a modern person dropped into a pre-industrial society with the
blueprints for everything up to about 1950 in your head. Research is free: you
already know how a steam engine works. Building is not. The goal node is
`point_contact_transistor`. Getting there is not the only thing worth doing.

## Your report

Write to `rome/playtest/reports/<CIV>_<ROLE>.md`. Structure it as:

```
# <CIV> / <ROLE>

## What I did
A few paragraphs. What was your plan, what actually happened, where did it turn.

## Result
Year reached or how it ended. Key numbers.

## FINDINGS
One numbered entry per finding, each in this shape:

### F1. <one line summary>
- **Severity**: BUG | UNREALISTIC | EXPLOIT | CONFUSING | WORKS-WELL
- **What I saw**: the exact commands and the exact replies
- **Why it is wrong** (or right): your reasoning
- **Reproduce**: the minimal sequence of commands
```

Be specific. "The economy felt off" is useless. "I bought 400 ha of forest for
100,000 den and the throttle did not move, here are the two state objects
before and after" is a finding I can act on.

A finding that the game got something RIGHT is worth reporting too, marked
WORKS-WELL, especially if you tried hard to break it and could not.

**Do not fix anything.** Do not edit any file outside
`rome/playtest/reports/`. You are testing, not repairing. If you find a crash,
report it with the reproduction; someone else will fix it.

## Honesty

Report what happened, not what you think should have happened. If you never got
the run working, say that. If you spent the whole session confused by the
protocol, that is itself the most important finding in the file. Do not invent
results and do not round a failure up into a success.
