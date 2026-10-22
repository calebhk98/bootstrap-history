"""command_words_unique: no alias may shadow another command's name, or the alias's handler answers for the command."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry
from sim.ui.proto import dispatch  # noqa: F401  (registers every command)

QUICK_TOPIC = True

handlers = command_registry.handlers()
shadowing = {alias: name for alias, name in command_registry.alias_map().items() if alias in command_registry.COMMANDS}
check("no alias is also a command name", shadowing == {}, shadowing)
wrong = [name for name, entry in command_registry.COMMANDS.items() if entry["handler"] is not None and handlers[name] is not entry["handler"]]
check("every command word reaches its own handler", wrong == [], wrong)
