# Module `interface`

The commands and figures a game offers its player. Added in phase 7 (not one of the 28 modules the catalogue counts): it replaces the last
process-global mod registries, which were the protocol's command table and the figure table.

**Status:** moved (`sim/interface/`).

## What it owns

Nothing saved. It owns one fact: which commands and figures this game has, after every provider's answer. The shipped commands and
figures stay shipped content, the tables `sim/ui` fills with `@command` and `@figure` when it loads; the module reads them and the mods'
data through its own provisions, so they are answers like any other.

| Published | Kind | Answer |
|---|---|---|
| `interface_declared` | table, constant for the game | `Declared`: `commands` (name to registry entry, patches applied), `owners` (word to mod id, empty for the game), `kinds`, `policies`, `figures`, `figure_owners` |

| Extension point | Combine | An answer is |
|---|---|---|
| `interface_commands` | list | `[CommandDeclaration]`: a command (shipped, code, data `read` or `macro`), a policy switch, or a patch to a command's help or its removal |
| `interface_figures` | list | `[FigureDeclaration]` |

| Provision | Point | What it answers |
|---|---|---|
| `interface.shipped` | `interface_commands`, `interface_figures` | the shipped tables (`sim.ui.api.shipped_commands`, `shipped_figures`) |
| `interface.data` | `interface_commands`, `interface_figures` | the mods' `data/ui/commands.json` and every `data/ui/figures.json` (bridge views `data_command_specs`, `data_figure_specs`) |

A mod's code provides with `api.command(...)` and `api.figure(...)`; a data mod needs no code.

## The clash rule

A command word (a name or an alias) belongs to its first declarer, and a figure name likewise. A second declarer is an error naming both
owners, raised when the game is built (`rules.declare`). Patches apply after every command is declared; a patch of a missing command, a
macro naming a missing command and a macro naming a macro are errors naming the mod.

## Readers

The protocol reads `command_registry.table_of(sim)` for the dispatch table, `help`, the typed parser (`parse_typed(line, table)`), the
field check, the seat address and the policies a year hook runs; the figures screens read `figures.figures_of(sim)`. A host with no
interface module (a stand-in game in a test) answers with the shipped tables. `KNOWN_COMMANDS`, `TYPED_ALIASES` and
`_AGENT_DISPATCH_TABLE` stay the shipped game's.

## Tests

`test_interface_rules` (the rule, one function), `test_mod_commands` and `test_complaint_423_figures_and_mine_goods_from_data` (data and
code declarations through a game's `Declared`), `test_mod_operations_smoke` (a mod's command and figure in its own game only).
