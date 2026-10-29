"""What the port reads of the map, each from a view the land module publishes. Mixed into `PortWorld`."""


class MapReads:
	"""One member per land view the port asks."""

	_needs: object

	@property
	def economy_map(self):
		"""The map the agent economy's setup holds for its tile builds and route searches (`EconomySetup.world_map`)."""
		return self._needs.map_for_agent_economy()

	def tiles_held_by(self, civilisation):
		return self._needs.tiles_listed_by(civilisation)

	def tile_description(self, tile):
		return self._needs.tile_description(tile)

	def tile_climates(self, tiles):
		return self._needs.tile_climates(tiles)

	def mode_crews(self, modes):
		return self._needs.mode_crews(modes)

	def modes_carrying(self, cargo):
		return self._needs.modes_carrying(cargo)

	def timber_on_tile(self, felled, tile):
		return self._needs.timber_on_tile(felled, tile)

	def deposit_catalogue(self):
		return self._needs.deposit_catalogue()

	def deposits_worked_before(self, tiles, resource_id, year, rates):
		return self._needs.deposits_worked_before(tiles, resource_id, year, rates)
