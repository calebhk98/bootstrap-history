"""The memo rule: an answer is reused while the world stamp and the entry's own inputs are unchanged."""
from typing import Any, Callable, Dict, Optional, Tuple

Stamp = Tuple[tuple, tuple]    # (objects compared by identity, values compared by equality)


def memoised(scope: Dict[str, Any], stamp: Optional[Stamp], key: Any, inputs: Any, compute: Callable[[], Any]) -> Any:
	"""`compute()` reused from `scope` while `stamp` holds and `inputs` equal those the entry was computed with.
	With no stamp (the world has nothing to compare) nothing is shared."""
	if stamp is None:
		return compute()
	objects, values = stamp
	held = scope.get("world")
	if held is None or held[1] != values or any(kept is not now for kept, now in zip(held[0], objects)):
		scope["world"] = (objects, values)
		scope["answers"] = {}
	answers = scope["answers"]
	entry = answers.get(key)
	if entry is not None and entry[0] == inputs:
		return entry[1]
	answer = compute()
	answers[key] = (inputs, answer)
	return answer
