# Bootstrap History

You are one person, dropped into a pre-industrial society (Rome in 100 AD by
default, or England, Han China, Norse Scandinavia, Mexica, or a civilisation
from a mod), carrying the knowledge of how modern technology works and none of
the industry that makes it. Knowing how a thing works is free. Building it
costs your own hours, other people's hours, money, materials and calendar
years you cannot buy back. You choose what to start and when to let a year
pass; the simulator works out what that costs, who you can hire, what the
society makes of you, and what history does to you meanwhile. The default goal
is the first transistor, and there are many other goals.

## Install

You need Python 3.11 or newer. The game uses only the standard library, so
there is nothing to `pip install`.

```bash
git clone <this repository>
cd <the folder you cloned into>
python3 sim/simulator.py validate      # optional check that the data loads
```

Run every command below from that folder. The folder can have any name.

## Start a game

```bash
python3 sim/simulator.py menu          # a menu: new game, load a game, options
python3 sim/simulator.py play          # go straight into a game
python3 sim/simulator.py civs          # list civilisations and starting kits
python3 sim/simulator.py goals         # list goals you can play toward
python3 sim/simulator.py --help        # every command
```

`play` takes options, and `play --help` lists them all. The common ones:

```bash
python3 sim/simulator.py play --civ england_1300 --kit merchant --goal <goal> --fog
```

- `--civ` picks the civilisation (see `civs`) and `--kit` the starting money.
- `--goal` picks what you are working toward (see `goals`).
- `--fog` hides everything except what you have built and could start next.
- `--mortal` lets the founder die of old age; by default you are immortal.
- `--seed` fixes the dice, so a game can be replayed.

## Playing

Type plain words, one command per line. The first ones to learn:

| Command | What it does |
|---|---|
| `state` | where you stand |
| `available` | what you could start today |
| `why <name>` | what a thing is, what it needs and what it costs |
| `start <name>` | begin it |
| `step <years>` | let time pass |
| `open <name>` | run a finished thing; finishing alone earns nothing |
| `path <goal>` | everything still standing between you and a goal |
| `stuck` | why you are not getting anywhere |
| `help` | more help; `help commands` lists every command |
| `quit` | leave |

You may type an item's name or its id. Money, hiring, buying, selling, risk
and policy screens are covered by `help commands`, `help labour` and
`help economy`.

## Saving

Add `--session FILE` and the game is written to that file after every command
and read back when you start again:

```bash
python3 sim/simulator.py play --civ rome_100ad --session mygame.json    # start a new saved game
echo "step 5" | python3 sim/simulator.py play --session mygame.json     # carry on from it
```

Inside a game, `save <file>` and `load <file>` do the same by hand, and the
menu's "Load a saved game" lists saves in your save folder. Set the folder
with the `ROME_SAVE_DIR` environment variable or from the menu's Options;
otherwise it is `.rome-saves` in your home directory. A save belongs to the
version that wrote it: after updating the game, start a new game.

## Mods

A mod is a folder in `mods/` with a `mod.json` inside. To install one, drop
the folder into `mods/`. To remove it, delete the folder or move it out. There
is no registry to edit, and mods run no code; they only add data.

A mod can add or change technologies, goals, production recipes, trades and
civilisations, and can remove existing ones. Things a mod adds are named
`<mod id>:<name>` and appear in the game like any other. Mods already installed
in `mods/` show up in `civs` and `goals`. If two mods clash, or one needs
another that is missing, the game refuses to load and the message names both.

To write a mod, read [mods/README.md](mods/README.md). It explains the mod id
format, what each file may contain, and how overrides and removal work.

## Reporting problems

Problems and ideas are files in [Complaints/](Complaints/). Read
`Complaints/README.md` for how to file one: a short markdown file with a title,
a status line, what went wrong and the command that shows it.

## For contributors

Read [CLAUDE.md](CLAUDE.md) first, then the design documents in
[docs/architecture/](docs/architecture/). The regression suite is
`python3 sim/test_regressions.py`.
