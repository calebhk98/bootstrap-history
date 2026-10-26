"""Errors the assembly raises; each names the modules and mods involved."""


class AssemblyError(ValueError):
	"""A module set that cannot be assembled: a missing or doubled provider, a removal something still reads."""


class StaleView(AssertionError):
	"""A cached view answered differently from a fresh computation: its owner changed state without bumping a channel."""
