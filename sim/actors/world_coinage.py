"""What a state asks about its coin when it decides whether to debase it."""


class CoinageView:
	"""Mixed into `ActorWorld`."""

	def coin_regime(self) -> str:
		"""The civilisation's coin standard: struck coin, weighed metal, a commodity or fiat."""
		return str((self.needs.civilisation().get("coin_standard") or {}).get("regime", ""))  # type: ignore[attr-defined]
