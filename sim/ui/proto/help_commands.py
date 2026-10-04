"""The `help commands` pages: a short index of groups, one group's commands, or the full listing in pages."""

from . import command_registry

JSON_MODE_NOTE = (
    "add the word 'json' to almost any command (or \"json\":true in a JSON "
    "command) to get its reply as the raw structured object instead of the "
    "rendered screen. 'compact' implies 'json' but is a short summary, not the "
    "full reply: 'state' and 'step' give year, money, net_per_year, "
    "founder_hours_free, projects (id, name, blocker), concerns (running, "
    "shut), standing, danger, goal, nearest_goal_blocker (and, for 'step', "
    "completed, lost and events); 'why' gives status, blocked_by and "
    "explanation; 'stuck' gives blockers. Other commands ignore 'compact'")


def _command_text(name, fog):
    entry = command_registry.COMMANDS[name]
    if fog and entry["fog_hidden"]:
        return "not available under fog of war"
    return "%s. %s" % (entry["summary"], entry["description"])


START_HERE = {
    "state": "where you stand", "available": "what you could begin today",
    "why <id>": "what a thing is for and what it costs", "start <id>": "begin it",
    "step <years>": "let time pass", "stuck": "why you are not getting on",
    "help sittings": "playing one command per process, saved between runs",
}
DEFAULT_PAGE = 40


def _group_line(names):
    shown = ", ".join(names[:6])
    return "%d commands: %s%s" % (len(names), shown, ", ..." if len(names) > 6 else "")


def index(sim):
    """The short default: the start-here block and one line per group."""
    groups = command_registry.grouped()
    return {
        "start here": {**START_HERE,
                       "the rest": "the groups below; help commands <group> lists one"},
        "groups": {group: _group_line(names) for group, names in groups.items()},
        "more": "help commands <group> for one group; help commands all for every "
                "command (pages: limit N offset N); help <command> for one command's usage",
    }


def group_page(sim, group):
    groups = command_registry.grouped()
    if group not in groups:
        near = command_registry.close_matches(group, list(groups))
        return {"no such group": group, "groups": list(groups),
                "did you mean": [word for word in near if word in groups]}
    names = groups[group]
    return {"group": group,
            "commands": {name: _command_text(name, sim.fog) for name in names},
            "usage": {name: command_registry.COMMANDS[name]["usage"] for name in names},
            "more": "help <command> for one command's usage and options"}


def full_listing(sim, limit=None, offset=0):
    """Every registered command; limit and offset page the commands, usage and groups."""
    names = list(command_registry.COMMANDS)
    page = {"start here": {**START_HERE,
                           "the rest": "everything below; help <command> shows one command's usage"}}
    shown = names
    if limit is not None:
        offset = max(0, offset or 0)
        shown = names[offset:offset + max(1, limit)]
        page["paging"] = {"total": len(names), "offset": offset, "shown": len(shown)}
        if offset + len(shown) < len(names):
            page["paging"]["next"] = "help commands all limit %d offset %d" % (limit, offset + len(shown))
    page.update({
        "commands": {"json / compact": JSON_MODE_NOTE,
                     **{name: _command_text(name, sim.fog) for name in shown}},
        "usage": {name: command_registry.COMMANDS[name]["usage"] for name in shown},
        "groups": command_registry.grouped(),
        "aliases": command_registry.alias_map(),
        "more": 'help <command> or help <alias> for one command\'s usage, '
                'options and description',
    })
    return page


def commands_page(sim, arguments):
    """`help commands` with its trailing words: <group>, all, limit N, offset N."""
    scope, numbers, words = None, {}, list(arguments)
    while words:
        word = words.pop(0)
        if word in ("limit", "offset") and words and words[0].isdigit():
            numbers[word] = int(words.pop(0))
        elif scope is None:
            scope = word
    if scope == "all" or (scope is None and numbers):
        return full_listing(sim, numbers.get("limit", DEFAULT_PAGE) if numbers else None,
                            numbers.get("offset", 0))
    return group_page(sim, scope) if scope not in (None, "index") else index(sim)
