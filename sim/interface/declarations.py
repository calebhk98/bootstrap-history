"""What a game declares to its player: commands (with their help and handlers) and figures, and who declared each."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

SHIPPED, CODE, READ, MACRO, POLICY, PATCH = "shipped", "code", "read", "macro", "policy", "patch"


@dataclass(frozen=True)
class CommandDeclaration:
	"""One command (or a patch to a command's help, or a policy switch) declared by `owner`: a mod id, empty for the game.
	`fields` are the registry entry's: group, summary, usage, description, options, aliases, fog_hidden, shape. A patch
	carries its data spec in `spec` and no handler; a policy carries its spec and neither fields nor handler."""
	owner: str
	name: str
	kind: str
	fields: Dict[str, Any] = field(default_factory=dict)
	handler: Optional[Callable] = None
	spec: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class FigureDeclaration:
	owner: str
	name: str
	label: str
	unit: str
	digits: int
	compute: Callable
	since: Optional[Callable] = None


@dataclass(eq=False)
class Declared:
	"""One game's commands and figures after every provider's answer."""
	commands: Dict[str, Dict[str, Any]] = field(default_factory=dict)   # name -> registry entry, in declaration order
	owners: Dict[str, str] = field(default_factory=dict)                # command name or alias -> owner ("" for the game)
	kinds: Dict[str, str] = field(default_factory=dict)                 # a mod's command name -> its kind
	policies: List[Tuple[str, Dict[str, Any]]] = field(default_factory=list)
	figures: Dict[str, Dict[str, Any]] = field(default_factory=dict)    # name -> {name, label, unit, digits, compute, since}
	figure_owners: Dict[str, str] = field(default_factory=dict)
