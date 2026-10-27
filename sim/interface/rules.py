"""The rules that turn every provider's declarations into one game's commands and figures.

A command word (a name or an alias) belongs to the first declarer; a second declarer is an error naming both. A patch
changes the help of a command that exists, or removes it, once every command is declared. A macro or policy may only name
commands that exist, and a macro may not name a macro."""
from typing import Any, Dict, List, Optional, Sequence

from sim.mod_errors import ModError

from .declarations import MACRO, PATCH, POLICY, SHIPPED, CommandDeclaration, Declared, FigureDeclaration

SHIPPED_OWNER = ""
DOCUMENTATION_FIELDS = ("group", "summary", "usage", "options", "description")


def owner_name(owner: str) -> str:
	return owner or "the shipped game"


def entry_fields(spec: Dict[str, Any], name: str) -> Dict[str, Any]:
	"""The registry fields of a command declared as data."""
	return dict(group=spec.get("group", "mods"), summary=spec["summary"], usage=spec.get("usage", [name]),
	            description=spec["description"], options=spec.get("options"), aliases=list(spec.get("aliases", ())),
	            fog_hidden=bool(spec.get("fog_hidden", False)), shape=spec.get("shape", "bare"))


def _entry(declaration: CommandDeclaration) -> Dict[str, Any]:
	fields = declaration.fields
	return {"name": declaration.name, "group": fields["group"], "summary": fields["summary"], "usage": list(fields["usage"]),
	        "description": fields["description"], "options": dict(fields.get("options") or {}), "aliases": list(fields.get("aliases", ())),
	        "handler": declaration.handler, "fog_hidden": fields.get("fog_hidden", False), "shape": fields.get("shape")}


def _claim(declared: Declared, word: str, owner: str) -> None:
	holder = declared.owners.get(word)
	if holder is not None:
		raise ModError("mod %s: the word %r is already taken by %s" % (owner, word, owner_name(holder)))
	declared.owners[word] = owner


def _resolve(declared: Declared, word: str) -> Optional[Dict[str, Any]]:
	word = (word or "").strip().lower()
	if word in declared.commands:
		return declared.commands[word]
	for entry in declared.commands.values():
		if word in entry["aliases"]:
			return entry
	return None


def _patch(declared: Declared, patch: CommandDeclaration) -> None:
	name, spec = patch.name, patch.spec or {}
	if name not in declared.commands:
		raise ModError("mod %s changes missing command %r" % (patch.owner, name))
	entry = declared.commands[name]
	if spec.get("remove") is True:
		for word in [name] + entry["aliases"]:
			declared.owners.pop(word, None)
		del declared.commands[name]
		return
	for documented in DOCUMENTATION_FIELDS:
		if documented in spec:
			entry[documented] = spec[documented]
	for alias in spec.get("aliases", ()):
		_claim(declared, alias, patch.owner)
		entry["aliases"].append(alias)


def declare_commands(declared: Declared, answers: Sequence[Sequence[CommandDeclaration]]) -> None:
	patches: List[CommandDeclaration] = []
	steps: Dict[str, Dict[str, Any]] = {}
	for answer in answers:
		for declaration in answer:
			if declaration.kind == PATCH:
				patches.append(declaration)
			elif declaration.kind == POLICY:
				declared.policies.append((declaration.name, declaration.spec))
			else:
				_claim(declared, declaration.name, declaration.owner)
				for alias in declaration.fields.get("aliases", ()):
					_claim(declared, alias, declaration.owner)
				declared.commands[declaration.name] = _entry(declaration)
				if declaration.kind != SHIPPED:
					declared.kinds[declaration.name] = declaration.kind
				if declaration.kind == MACRO:
					steps[declaration.name] = declaration.spec
	for patch in patches:
		_patch(declared, patch)
	_check_macros(declared, steps)


def _check_macros(declared: Declared, macros: Dict[str, Dict[str, Any]]) -> None:
	checked = dict(macros)
	checked.update({name: spec for name, spec in declared.policies})
	for name, spec in checked.items():
		for step in spec.get("steps") or spec.get("do") or ():
			target = _resolve(declared, step["cmd"])
			if target is None:
				raise ModError("mod command %s names command %r, which does not exist (removed, or the "
				               "mod's code is not allowed; see `simulator.py validate`)" % (name, step["cmd"]))
			if declared.kinds.get(target["name"]) == MACRO:
				raise ModError("mod command %s names the macro %s; a macro may not name a macro" % (name, target["name"]))


def declare_figures(declared: Declared, answers: Sequence[Sequence[FigureDeclaration]]) -> None:
	for answer in answers:
		for figure in answer:
			if figure.name in declared.figures:
				raise ModError("mod %s: the figure %r is already declared by %s" % (
					figure.owner or "the shipped game", figure.name, owner_name(declared.figure_owners[figure.name])))
			declared.figures[figure.name] = {"name": figure.name, "label": figure.label, "unit": figure.unit, "digits": figure.digits,
			                                 "compute": figure.compute, "since": figure.since}
			declared.figure_owners[figure.name] = figure.owner


def declare(command_answers: Sequence[Sequence[CommandDeclaration]], figure_answers: Sequence[Sequence[FigureDeclaration]]) -> Declared:
	"""One game's commands and figures from every provider's answers, in provider order (the game's own first, then the mods')."""
	declared = Declared()
	declare_commands(declared, command_answers)
	declare_figures(declared, figure_answers)
	return declared
