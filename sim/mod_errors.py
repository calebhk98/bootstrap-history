"""The error a mod's content raises when it cannot be loaded or applied; shared by the engine and the packages a mod reaches."""


class ModError(ValueError):
    """A mod cannot be loaded without making an ambiguous choice."""
