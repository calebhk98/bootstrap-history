"""The command registry: each command declares its own help beside its handler.

`@command(...)` on a handler records the name, group, summary, usage,
options, description, aliases and (for the typed parser) argument shape. The dispatch table, KNOWN_COMMANDS, the
typed alias map and every `help` page are all read from this registry, so a
command cannot run without also being documented.
"""

import difflib

# Groups in the order `help commands` shows them; an unlisted group follows.
GROUP_ORDER = ("overview", "projects", "labour", "money", "society", "game")

COMMANDS = {}   # name -> entry dict, in registration order


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


def names_with_shape(*shapes):
    """Names of the commands declaring any of these argument shapes."""
    return tuple(name for name, entry in COMMANDS.items() if entry["shape"] in shapes)


def handlers():
    """Every accepted word (command or alias) mapped to its handler."""
    table = {}
    for name, entry in COMMANDS.items():
        if entry["handler"] is None:
            continue
        table[name] = entry["handler"]
        for alias in entry["aliases"]:
            table[alias] = entry["handler"]
    return table


def alias_map():
    """Every alias mapped to the command it stands for."""
    return {alias: name for name, entry in COMMANDS.items()
            for alias in entry["aliases"]}


def resolve(word):
    """The registry entry a command name or alias stands for, or None."""
    word = (word or "").strip().lower()
    if word in COMMANDS:
        return COMMANDS[word]
    name = alias_map().get(word)
    return COMMANDS[name] if name else None


def close_matches(word, extra_words=()):
    """Command names, aliases and extra words that look like `word`."""
    word = (word or "").strip().lower()
    pool = list(dict.fromkeys(list(COMMANDS) + list(alias_map()) + list(extra_words)))
    matches = difflib.get_close_matches(word, pool, n=4, cutoff=0.6)
    matches += [candidate for candidate in pool
                if len(word) >= 3 and candidate.startswith(word[:3])
                and candidate not in matches]
    return matches[:5]


def grouped():
    """Command names by group, in display order."""
    groups = {}
    for name, entry in COMMANDS.items():
        groups.setdefault(entry["group"], []).append(name)
    ordered = [group for group in GROUP_ORDER if group in groups]
    ordered += [group for group in groups if group not in GROUP_ORDER]
    return {group: groups[group] for group in ordered}


def page(name, fog=False):
    """The JSON help page for one command."""
    entry = COMMANDS[name]
    description = entry["description"]
    if fog and entry["fog_hidden"]:
        description = "Not available under fog of war. " + description
    return {
        "name": name, "group": entry["group"], "summary": entry["summary"],
        "usage": list(entry["usage"]), "options": dict(entry["options"]),
        "description": description, "aliases": list(entry["aliases"]),
    }
