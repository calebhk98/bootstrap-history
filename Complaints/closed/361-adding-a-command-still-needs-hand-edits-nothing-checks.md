# Adding a command still needs hand edits that nothing checks

**Status:** closed - pinned by sim/tests/test_command_discovery.py (discovery, derived parsers, usage parses, and the help pages name only registered commands; the command index shows registered text with no hand override)

Commands are declared once (`@command` in `proto/dispatch_*.py`), and `help`, the command lists and aliases are generated from the registry. But a new command also needs an import in `dispatch.py` when it lives in a new module, a parser entry in `typed.py` `_COMMAND_PARSERS` (or its arguments are dropped), an entry in the id-taking command lists, and a line in `sim/PROTOCOL.md`; the help front page and the typed-play options entry are hand text. Nothing checks these.

Fix: load dispatch modules by discovery, let a command declare its argument shape so the typed parser is derived, and a test that every registered command parses its documented usage and appears in PROTOCOL.md (or generate that section).
