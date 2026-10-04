"""Typed-line parsing for pursue and programme: key:value caps, `preview`, and the goal in the rest."""

NUMBER_KEYS = ("max_total_cost", "max_annual_draw", "reserve_cash", "limit")


def _split(words):
    """(options, remaining words, error) from tokens like max_total_cost:500, limit=3 and preview."""
    options, remaining = {}, []
    for word in words:
        text = str(word)
        key, separator, value = text.replace("=", ":", 1).partition(":")
        if separator and key.lower() in NUMBER_KEYS:
            try:
                options[key.lower()] = float(value.replace(",", ""))
            except ValueError:
                return None, None, "'%s' is not a number for %s" % (value, key)
        elif text.lower() in ("preview", "dry_run"):
            options["preview"] = True
        else:
            remaining.append(text)
    if "limit" in options:
        options["limit"] = int(options["limit"])
    return options, remaining, None


def parse_pursue(command, rest, words, nums, want_json):
    options, remaining, error = _split(rest)
    if error:
        return None, error
    out = {"cmd": "pursue", **options}
    if remaining:
        out["goal"] = " ".join(remaining)
    return out, None


def parse_programme(command, rest, words, nums, want_json):
    options, remaining, error = _split(rest)
    if error:
        return None, error
    out = {"cmd": "programme", "action": remaining[0].lower() if remaining else "show", **options}
    if len(remaining) > 1:
        out["target"] = " ".join(remaining[1:])
    return out, None
