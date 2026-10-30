"""The command registry: each command declares its own help beside its handler.

`@command(...)` on a handler records the name, group, summary, usage,
options, description, aliases and (for the typed parser) argument shape. The dispatch table, KNOWN_COMMANDS, the
typed alias map and every `help` page are all read from this registry, so a
command cannot run without also being documented.
"""

import difflib
import weakref

# Groups in the order `help commands` shows them; an unlisted group follows.
GROUP_ORDER = ("overview", "projects", "labour", "money", "society", "game")

COMMANDS = {}   # the shipped commands: name -> entry dict, in registration order (a game's own table: `table_of`)


def register_command(name, group, summary, usage, description,
                     options=None, aliases=(), handler=None, fog_hidden=False,
                     shape=None):
    """Record one command. `usage` is a list of example forms, `options`
    maps an argument or option to its meaning. `shape` names the typed
    argument form when it is a plain one (typed.py maps shapes to parsers):
    "bare" takes none, "tech" names a technology (fog-guarded), "tech_done"
    names one already done, "file" a file name, "word" one word, "text" free
    prose kept verbatim (the words json and compact are not read as output modes). A command
    with its own parser in typed.py leaves it unset."""
    assert name not in COMMANDS, "command %r registered twice" % name
    COMMANDS[name] = {
        "name": name, "group": group, "summary": summary,
        "usage": list(usage), "description": description,
        "options": dict(options or {}), "aliases": list(aliases),
        "handler": handler, "fog_hidden": fog_hidden, "shape": shape,
    }
    return COMMANDS[name]


def command(name, **fields):
    """Decorator form of register_command for a handler function."""
    def decorate(handler):
        register_command(name, handler=handler, **fields)
        return handler
    return decorate


def unregister(name):
    COMMANDS.pop(name, None)


def shipped_commands():
    """The shipped commands, for the interface module to declare."""
    return list(COMMANDS.values())


class CommandTable:
    """The commands of one game (its entries and its mods' policy switches), read by every screen that lists, parses or runs one."""

    def __init__(self, commands, policies=()):
        self.commands = commands
        self.policies = list(policies)

    def names_with_shape(self, *shapes):
        """Names of the commands declaring any of these argument shapes."""
        return tuple(name for name, entry in self.commands.items() if entry["shape"] in shapes)

    def handlers(self):
        """Every accepted word (command or alias) mapped to its handler."""
        table = {}
        for name, entry in self.commands.items():
            if entry["handler"] is None:
                continue
            table[name] = entry["handler"]
            for alias in entry["aliases"]:
                table[alias] = entry["handler"]
        return table

    def unknown_command_error(self, command):
        """The refusal for a word that is no command: it names every command there is, so the list cannot go stale."""
        return "unknown cmd %r. Use one of: %s. %s" % (
            command, ", ".join(self.commands), 'Or {"cmd":"help"} for what each one does.')

    def alias_map(self):
        """Every alias mapped to the command it stands for."""
        return {alias: name for name, entry in self.commands.items()
                for alias in entry["aliases"]}

    def resolve(self, word):
        """The registry entry a command name or alias stands for, or None."""
        word = (word or "").strip().lower()
        if word in self.commands:
            return self.commands[word]
        name = self.alias_map().get(word)
        return self.commands[name] if name else None

    def close_matches(self, word, extra_words=()):
        """Command names, aliases and extra words that look like `word`."""
        word = (word or "").strip().lower()
        pool = list(dict.fromkeys(list(self.commands) + list(self.alias_map()) + list(extra_words)))
        matches = difflib.get_close_matches(word, pool, n=4, cutoff=0.6)
        matches += [candidate for candidate in pool
                    if len(word) >= 3 and candidate.startswith(word[:3])
                    and candidate not in matches]
        return matches[:5]

    def grouped(self):
        """Command names by group, in display order."""
        groups = {}
        for name, entry in self.commands.items():
            groups.setdefault(entry["group"], []).append(name)
        ordered = [group for group in GROUP_ORDER if group in groups]
        ordered += [group for group in groups if group not in GROUP_ORDER]
        return {group: groups[group] for group in ordered}

    def page(self, name, fog=False):
        """The JSON help page for one command."""
        entry = self.commands[name]
        description = entry["description"]
        if fog and entry["fog_hidden"]:
            description = "Not available under fog of war. " + description
        return {
            "name": name, "group": entry["group"], "summary": entry["summary"],
            "usage": list(entry["usage"]), "options": dict(entry["options"]),
            "description": description, "aliases": list(entry["aliases"]),
        }


# The shipped game's table, over the registry the `@command` decorators fill when the handlers load.
SHIPPED = CommandTable(COMMANDS)
names_with_shape = SHIPPED.names_with_shape
handlers = SHIPPED.handlers
unknown_command_error = SHIPPED.unknown_command_error
alias_map = SHIPPED.alias_map
resolve = SHIPPED.resolve
close_matches = SHIPPED.close_matches
grouped = SHIPPED.grouped
page = SHIPPED.page

_TABLES = weakref.WeakKeyDictionary()   # a game's declared commands -> its table


def table_of(sim):
    """The commands of the game `sim`: the shipped ones and its mods', after the mods' patches (the interface module's
    view). A host with no interface module answers with the shipped table."""
    try:
        declared = sim.view("interface_declared")
    except (AttributeError, KeyError):
        return SHIPPED
    declared = declared()
    table = _TABLES.get(declared)
    if table is None:
        table = _TABLES[declared] = CommandTable(declared.commands, declared.policies)
    return table
