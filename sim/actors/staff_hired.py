"""The people the labour core hired for each actor; kept apart from the engine's year of the economy, which never reads an actor's record."""


def set_staff(registry, staff_by_actor):
	"""Every actor's workforce becomes the people hired for it (`staff_by_actor`: actor id -> {trade: people}); an actor
	not named has none."""
	for actor_id, actor in sorted(registry.actors.items()):
		actor.record.workforce.clear()
		actor.record.workforce.update(staff_by_actor.get(actor_id, {}))
	registry.refresh_staff()
