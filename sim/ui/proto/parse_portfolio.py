"""Typed-line parser for `portfolio`: a group word, `all`, `offset:K`, `limit:N` (Complaints/88)."""
from . import typed


def _parse_portfolio(command, rest, words, nums, want_json):
    out = {"cmd": "portfolio", "json": want_json}
    group_words = []
    for word in rest:
        text = str(word).lower()
        key, _, value = text.partition(":")
        if key in ("limit", "offset") and value.isdigit():
            out[key] = int(value)
        elif text == "all":
            out["all"] = True
        elif text not in ("json", "compact"):
            group_words.append(text)
    if group_words:
        out["group"] = "_".join(group_words)
    return out, None


typed._COMMAND_PARSERS["portfolio"] = _parse_portfolio
