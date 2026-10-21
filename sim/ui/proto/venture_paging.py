"""Paging of the shut-concern list of `ventures`, like `available` and `log`: a short default screen that says how many
more there are and the command for the next page."""


def page_request(cmd, default_limit):
    """(offset, limit) a `ventures` command asks for: never below zero or one, the default when absent or not a number."""
    try:
        offset = max(0, int(cmd.get("offset", 0)))
    except (TypeError, ValueError):
        offset = 0
    try:
        limit = int(cmd.get("limit", 0)) or default_limit
    except (TypeError, ValueError):
        limit = default_limit
    return offset, max(1, limit)


def page_fields(total, offset, limit):
    """The reply fields that say where the page sits: how many shut concerns in all, where it starts, and (only when
    there are more past it) how many more and the command for the next page."""
    out = {"shut_concerns_in_all": total, "showing_from": offset}
    if total > offset + limit:
        out["and_more_you_could_open"] = total - offset - limit
        out["next_page"] = "ventures offset:%d limit:%d" % (offset + limit, limit)
    return out
