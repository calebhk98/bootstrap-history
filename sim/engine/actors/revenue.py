"""A state's revenue: each form its civilisation declares, assessed on the base it names.

    revenue of a form = rate of the form * base the form is assessed on

A form is paid in coin, or in kind when it names the good (`paid_in`): a share of the harvest is taken as
grain, which goes to the state's stores and is used or sold through the goods market (government.py).
"""
from dataclasses import dataclass
from typing import Any, List

from .revenue_bases import BASES


@dataclass(frozen=True)
class Assessment:
	form: str
	basis: str
	base: float  # money's worth of the base
	rate: float  # share of the base the state takes
	money: float  # money's worth of what it takes
	tonnes: float = 0.0  # what is taken in kind, in tonnes; zero for a form paid in coin
	material: str = ""  # the good taken in kind

	@property
	def in_kind(self) -> bool:
		return bool(self.material)


def assess(world: Any) -> List[Assessment]:
	"""Every declared form assessed on this year's base, in the order the civilisation lists them."""
	assessments = []
	for declared in world.revenue_forms():
		base = BASES[declared["basis"]](world)
		rate = float(declared["rate"])
		material = declared.get("paid_in", "")
		if material and material != base.material:
			raise ValueError("form %r is paid in %r but its basis %r yields %r"
							 % (declared["form"], material, declared["basis"], base.material))
		assessments.append(Assessment(declared["form"], declared["basis"], base.value, rate, rate * base.value,
									  rate * base.tonnes if material else 0.0, material))
	return assessments
