"""Typed-line parsing for pay: `pay state debt`, `pay state claims`, `pay state 500`."""
from . import typed


def parse_pay(command, rest, words, nums, want_json):
    kept = [str(word) for word in rest if str(word).lower() not in ("state", "the", "to")]
    if kept and kept[0].lower() in ("debt", "claims"):
        return {"cmd": "pay", "what": kept[0].lower()}, None
    if not nums:
        return None, "pay needs `debt`, `claims` or an amount, e.g. 'pay state debt' or 'pay state 500'."
    return {"cmd": "pay", "amount": nums[0]}, None


typed._COMMAND_PARSERS.setdefault("pay", parse_pay)
