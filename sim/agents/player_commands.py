"""A player's commands: plain dicts queued in `record.orders`, run in order on its turn.

Each command names a handler in the game's command table (the actors module's `player_commands` point; a mod adds one by
providing to it). A handler is
`handler(player, order, world) -> detail text` and refuses by raising `CommandRejected`. Every
command, run or refused, leaves one entry in the player's journal. A handler checks its own input and refuses; an
error it raises is a bug in the handler and is not caught.
"""
from typing import Any, Callable, Dict

from .tuning_player import PLAYER_JOURNAL_LIMIT


class CommandRejected(Exception):
	"""A command that cannot be carried out; the message is the reason."""


def number_of(value: Any, what: str) -> float:
	"""A number an order carries, as a float; refuses what is not one."""
	if isinstance(value, bool) or not isinstance(value, (int, float, str)):
		raise CommandRejected("%s must be a number" % what)
	try:
		return float(value)
	except ValueError as reason:
		raise CommandRejected("%s must be a number" % what) from reason


def write_journal(player: Any, year: int, name: Any, ok: bool, detail: str) -> None:
	"""Append a result, keeping only the most recent entries."""
	journal = player.record.journal
	journal.append({"year": year, "command": name, "ok": ok, "detail": detail})
	del journal[:max(0, len(journal) - PLAYER_JOURNAL_LIMIT)]


def run_orders(player: Any, world: Any) -> None:
	"""Run and clear the player's queued orders, journalling each."""
	orders = list(player.record.orders)
	player.record.orders.clear()
	commands = player.command_table
	if commands is None:   # a player made outside a registry runs the shipped commands
		from .shipped import shipped_commands
		commands = shipped_commands()
	for order in orders:
		name = order.get("command") if isinstance(order, dict) else None
		handler = commands.get(name) if isinstance(name, str) else None
		if handler is None:
			write_journal(player, world.setting.year, name, False, "unknown command")
			continue
		try:
			detail = handler(player, order, world)
		except CommandRejected as reason:
			write_journal(player, world.setting.year, name, False, str(reason))
		else:
			write_journal(player, world.setting.year, name, True, detail or "")


def _node_of(order: Dict[str, Any]) -> str:
	node_id = order.get("node")
	if not isinstance(node_id, str) or not node_id:
		raise CommandRejected("no node given")
	return node_id


def research(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.copying.start_research(_node_of(order), world)


def open_concern(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.begin_concern(_node_of(order), world)


def close_concern(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.end_concern(_node_of(order), world)


def transfer(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.send_money(order.get("to"), number_of(order.get("amount", 0.0), "amount"))


def base_commands() -> Dict[str, Callable[[Any, Dict[str, Any], Any], str]]:
	return {"research": research, "open": open_concern, "close": close_concern, "transfer": transfer}
