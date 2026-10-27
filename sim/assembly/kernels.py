"""Kernels: engine computations a mod may replace, each a plain function the owning module calls through the assembly.

A kernel is declared by one module (`ModuleSpec.kernels`) as a name `<module_id>.<name>`, the reference function (the
engine's own code, moved), a description of its input and output, a function that builds its stored sample inputs and a
tolerance (zero: exact) with its reason. A mod's replacement is accepted only when it answers every sample as the
reference does; the module is handed the bound function, the replacement when there is one."""
import math
from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence, Tuple

from .errors import AssemblyError

Sample = Tuple[tuple, dict]      # (positional arguments, keyword arguments) of one call


@dataclass(frozen=True)
class Kernel:
	name: str                                          # "<module_id>.<name>"
	reference: Callable                                # the plain function the engine ran before it was a kernel
	inputs: str                                        # what the arguments are
	output: str                                        # what the answer is
	samples: Callable[[], Sequence[Sample]]            # builds fresh sample calls each time (a call may consume its arguments)
	tolerance: float = 0.0                             # relative tolerance on every float of the answer; 0: exact
	tolerance_reason: str = ""                         # why a replacement may differ by that much (required when tolerance > 0)
	observe: Optional[Callable[[tuple, dict, Any], Any]] = None   # (args, kwargs, answer) -> the part of the answer that is contractual

	def __post_init__(self) -> None:
		if "." not in self.name:
			raise AssemblyError("kernel %s: its name is <module_id>.<name>" % self.name)
		if self.tolerance < 0.0 or (self.tolerance > 0.0 and not self.tolerance_reason):
			raise AssemblyError("kernel %s: a tolerance needs a reason (and may not be negative)" % self.name)


def same(reference: Any, found: Any, tolerance: float) -> bool:
	"""Whether two answers agree: equal, floats within `tolerance` of the larger (floor one) when it is above zero."""
	if isinstance(reference, float) or isinstance(found, float):
		if not isinstance(reference, (int, float)) or not isinstance(found, (int, float)):
			return False
		if math.isnan(reference) or math.isnan(found):
			return math.isnan(reference) and math.isnan(found)
		if reference == found:
			return True
		return tolerance > 0.0 and math.isfinite(reference) and math.isfinite(found) \
			and abs(reference - found) <= tolerance * max(abs(reference), abs(found), 1.0)
	if isinstance(reference, dict):
		return isinstance(found, dict) and list(reference) == list(found) \
			and all(same(reference[key], found[key], tolerance) for key in reference)
	if isinstance(reference, (list, tuple)):
		return isinstance(found, (list, tuple)) and len(reference) == len(found) \
			and all(same(first, second, tolerance) for first, second in zip(reference, found))
	return bool(reference == found) and type(reference) is type(found)


def _answer(kernel: Kernel, function: Callable, sample: Sample) -> Any:
	arguments, keywords = sample
	answer = function(*arguments, **keywords)
	return answer if kernel.observe is None else kernel.observe(arguments, keywords, answer)


def check_replacement(kernel: Kernel, mod_id: str, function: Callable) -> None:
	"""Run the replacement and the reference on the kernel's samples; AssemblyError naming the mod and the kernel
	when the replacement fails or answers differently on any of them."""
	if not callable(function):
		raise AssemblyError("mod %s replaces the kernel %s with something that is not callable" % (mod_id, kernel.name))
	if not kernel.samples():
		raise AssemblyError("kernel %s has no samples, so mod %s's replacement cannot be checked" % (kernel.name, mod_id))
	for index, (expected, offered) in enumerate(zip(kernel.samples(), kernel.samples())):
		wanted = _answer(kernel, kernel.reference, expected)
		try:
			found = _answer(kernel, function, offered)
		except Exception as error:   # a replacement may fail in any way; the refusal says how
			raise AssemblyError("mod %s's kernel %s raised %s on sample %d: %s" % (mod_id, kernel.name, type(error).__name__, index, error))
		if not same(wanted, found, kernel.tolerance):
			raise AssemblyError("mod %s's kernel %s answers sample %d differently from the reference (%s vs %s; %s)" % (
				mod_id, kernel.name, index, _short(found), _short(wanted),
				"exact" if kernel.tolerance == 0.0 else "tolerance %g: %s" % (kernel.tolerance, kernel.tolerance_reason)))


def _short(value: Any) -> str:
	text = repr(value)
	return text if len(text) <= 80 else text[:77] + "..."
