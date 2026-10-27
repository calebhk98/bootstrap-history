"""What a game adds to its actors: the kinds of actor, the yearly founding rules, the policies and the players' commands.

The actors module owns five extension points and hands the registry what their providers answered, combined here. A later
answer replaces an earlier one of the same name (kind, policy, command, spawner); the world scope is the first one given."""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

Spawner = Callable[[Any, Any], List[str]]


@dataclass
class ActorExtensions:
	kinds: Dict[str, Any] = field(default_factory=dict)                   # kind -> the class that builds its actors
	spawners: List[Tuple[str, Spawner]] = field(default_factory=list)     # run after every actor's year, in this order
	world_scope: Optional[Callable[[Any, Any, Any], Any]] = None          # (world, profile, registry) -> the world a country's actors see
	policies: Dict[str, Callable[[], Any]] = field(default_factory=dict)  # policy kind -> factory
	commands: Dict[str, Callable[[Any, Dict[str, Any], Any], str]] = field(default_factory=dict)   # (player, order, world) -> detail


def combine(kinds: Sequence[Dict[str, Any]], spawners: Sequence[Sequence[Tuple[str, Spawner]]], world_scope: Optional[Callable],
            policies: Sequence[Dict[str, Callable]], commands: Sequence[Dict[str, Callable]]) -> ActorExtensions:
	"""The providers' answers of the five points, each list in provider order, merged into one set."""
	combined = ActorExtensions(world_scope=world_scope)
	for answer in kinds:
		combined.kinds.update(answer)
	for answer in spawners:
		for name, spawner in answer:
			for index, (existing, _old) in enumerate(combined.spawners):
				if existing == name:
					combined.spawners[index] = (name, spawner)
					break
			else:
				combined.spawners.append((name, spawner))
	for answer in policies:
		combined.policies.update(answer)
	for answer in commands:
		combined.commands.update(answer)
	return combined
