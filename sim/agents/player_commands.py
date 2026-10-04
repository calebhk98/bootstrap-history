"""A player's commands: plain dicts queued in `record.orders`, run in order on its turn.

Each command names a handler in `COMMANDS`; a mod adds one with `register_command`. A handler is
`handler(player, order, world) -> detail text` and refuses by raising `CommandRejected`. Every
command, run or refused, leaves one entry in the player's journal; nothing here raises to the caller.
"""
from typing import Any, Callable, Dict

from .tuning_player import PLAYER_JOURNAL_LIMIT


class CommandRejected(Exception):
	"""A command that cannot be carried out; the message is the reason."""


COMMANDS: Dict[str, Callable[[Any, Dict[str, Any], Any], str]] = {}


def register_command(name: str, handler: Callable[[Any, Dict[str, Any], Any], str]) -> None:
	"""Make `{"command": name, ...}` run `handler`; registering a name again replaces it."""
	COMMANDS[name] = handler


def write_journal(player: Any, year: int, name: Any, ok: bool, detail: str) -> None:
	"""Append a result, keeping only the most recent entries."""
	journal = player.record.journal
	journal.append({"year": year, "command": name, "ok": ok, "detail": detail})
	del journal[:max(0, len(journal) - PLAYER_JOURNAL_LIMIT)]


def run_orders(player: Any, world: Any) -> None:
	"""Run and clear the player's queued orders, journalling each."""
	orders = list(player.record.orders)
	player.record.orders.clear()
	for order in orders:
		name = order.get("command") if isinstance(order, dict) else None
		handler = COMMANDS.get(name) if isinstance(name, str) else None
		if handler is None:
			write_journal(player, world.year, name, False, "unknown command")
			continue
		try:
			detail = handler(player, order, world)
		except CommandRejected as reason:
			write_journal(player, world.year, name, False, str(reason))
		except (KeyError, TypeError, ValueError, AttributeError) as error:
			write_journal(player, world.year, name, False, "invalid command: %s %s" % (type(error).__name__, error))
		else:
			write_journal(player, world.year, name, True, detail or "")


def _node_of(order: Dict[str, Any]) -> str:
	node_id = order.get("node")
	if not isinstance(node_id, str) or not node_id:
		raise CommandRejected("no node given")
	return node_id


def research(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.start_research(_node_of(order), world)


def open_concern(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.begin_concern(_node_of(order), world)


def close_concern(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.end_concern(_node_of(order), world)


def transfer(player: Any, order: Dict[str, Any], world: Any) -> str:
	return player.send_money(order.get("to"), float(order.get("amount", 0.0)))


register_command("research", research)
register_command("open", open_concern)
register_command("close", close_concern)
register_command("transfer", transfer)
