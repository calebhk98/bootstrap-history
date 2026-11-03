"""Answers that hold for the whole of one yearly turn: the part that owns a table of them asks through this."""
from typing import Any, Callable, Dict


def once(memo: Dict[str, Any], key: str, compute: Callable[[], Any]) -> Any:
	"""`compute()` the first time `key` is asked of `memo`, the kept answer after."""
	if key not in memo:
		memo[key] = compute()
	return memo[key]
