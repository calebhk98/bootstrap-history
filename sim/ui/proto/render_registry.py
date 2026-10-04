"""Renderers that register themselves: `@renders("anatomy", "metric")` above a render function.

render_typed imports every render_*.py module in this package, so a new screen adds its renderer in
its own file and edits no shared table."""
RENDERERS = {}


def renders(*command_names):
    def register(function):
        for command_name in command_names:
            RENDERERS[command_name] = function
        return function
    return register
