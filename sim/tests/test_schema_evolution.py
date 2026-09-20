"""Schema-evolution and automatic type-driven persistence regression tests.

Proves that adding a persistent field using supported types (Set, Dict, List,
Tuple, Counter, defaultdict, ActiveProjectState, Optional, primitive scalars)
automatically saves and loads with exact type and value parity without needing
field-name-specific registration or special cases.
"""
import collections
from dataclasses import dataclass, field
from typing import Any, DefaultDict, Dict, List, Optional, Set, Tuple

from sim.engine.state import (
	ActiveProjectState,
	HouseholdState,
	deserialize_state,
	serialize_state,
)
from sim.tests.harness import check


@dataclass
class SerializationProbe:
	"""Probe dataclass with representative supported persistent types."""
	scalar: int = 123
	names: Set[str] = field(default_factory=lambda: {"alpha", "beta"})
	mapping: Dict[str, float] = field(default_factory=lambda: {"x": 1.5, "y": 2.5})
	values: List[int] = field(default_factory=lambda: [1, 2, 3])
	counts: collections.Counter = field(default_factory=lambda: collections.Counter({"item_a": 4, "item_b": 2}))
	optional_val: Optional[str] = "present"
	optional_none: Optional[int] = None
	pair: Tuple[str, float] = ("weight", 42.0)
	nested_proj: ActiveProjectState = field(
		default_factory=lambda: ActiveProjectState(ph_left=50.0, cost_left=100.0, lab_left={"smith": 10.0})
	)


def _test_generic_serialization_probe():
	"""Verify SerializationProbe round-trips with exact types and values."""
	probe = SerializationProbe()
	blob = serialize_state(probe)

	restored = deserialize_state(blob, target_type=SerializationProbe)
	if not isinstance(restored, SerializationProbe):
		return False, f"Expected SerializationProbe instance, got: {type(restored)}"

	# 1. Scalar
	if restored.scalar != 123 or not isinstance(restored.scalar, int):
		return False, f"Scalar failed: {restored.scalar} ({type(restored.scalar)})"

	# 2. Set
	if restored.names != {"alpha", "beta"} or not isinstance(restored.names, set):
		return False, f"Set failed: {restored.names} ({type(restored.names)})"

	# 3. Dict
	if restored.mapping != {"x": 1.5, "y": 2.5} or not isinstance(restored.mapping, dict):
		return False, f"Dict failed: {restored.mapping} ({type(restored.mapping)})"

	# 4. List
	if restored.values != [1, 2, 3] or not isinstance(restored.values, list):
		return False, f"List failed: {restored.values} ({type(restored.values)})"

	# 5. Counter
	if restored.counts != collections.Counter({"item_a": 4, "item_b": 2}) or not isinstance(restored.counts, collections.Counter):
		return False, f"Counter failed: {restored.counts} ({type(restored.counts)})"

	# 6. Optional
	if restored.optional_val != "present" or restored.optional_none is not None:
		return False, f"Optional failed: val={restored.optional_val}, none={restored.optional_none}"

	# 7. Tuple
	if restored.pair != ("weight", 42.0) or not isinstance(restored.pair, tuple):
		return False, f"Tuple failed: {restored.pair} ({type(restored.pair)})"

	# 8. Nested ActiveProjectState
	if not isinstance(restored.nested_proj, ActiveProjectState):
		return False, f"Nested project failed to reconstruct as ActiveProjectState: {type(restored.nested_proj)}"
	if restored.nested_proj.ph_left != 50.0 or restored.nested_proj.lab_left.get("smith") != 10.0:
		return False, f"Nested project values failed: {restored.nested_proj}"

	return True, "Generic serialization probe round-tripped with exact types and values"


_ok, _detail = _test_generic_serialization_probe()
check("SerializationProbe round-trip with exact types", _ok, _detail)


def _test_schema_evolution_unregistered_set():
	"""Verify an unregistered Set field on a real dataclass reconstructs as set, not dict."""
	@dataclass
	class ExtendedHouseholdState(HouseholdState):
		temporary_test_set: Set[str] = field(default_factory=lambda: {"alpha", "beta"})

	orig = ExtendedHouseholdState(capital=100.0, temporary_test_set={"alpha", "beta"})
	blob = serialize_state(orig)
	restored = deserialize_state(blob, target_type=ExtendedHouseholdState)

	if not isinstance(restored.temporary_test_set, set):
		return False, f"Unregistered set field deserialized as {type(restored.temporary_test_set)} instead of set: {restored.temporary_test_set}"
	if restored.temporary_test_set != {"alpha", "beta"}:
		return False, f"Unregistered set field contents mismatch: {restored.temporary_test_set}"

	return True, "Unregistered set field on dataclass reconstructed automatically"


_ok, _detail = _test_schema_evolution_unregistered_set()
check("Unregistered set field on dataclass reconstructed as set", _ok, _detail)


def _test_empty_collections_round_trip():
	"""Verify empty collections (set, dict, list, Counter, defaultdict) preserve types when empty."""
	@dataclass
	class EmptyProbe:
		empty_set: Set[str] = field(default_factory=set)
		empty_dict: Dict[str, float] = field(default_factory=dict)
		empty_list: List[int] = field(default_factory=list)
		empty_counter: collections.Counter = field(default_factory=collections.Counter)
		empty_defaultdict: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int))

	orig = EmptyProbe()
	blob = serialize_state(orig)
	restored = deserialize_state(blob, target_type=EmptyProbe)

	if not isinstance(restored.empty_set, set) or len(restored.empty_set) != 0:
		return False, f"Empty set failed: {restored.empty_set} ({type(restored.empty_set)})"
	if not isinstance(restored.empty_dict, dict) or len(restored.empty_dict) != 0:
		return False, f"Empty dict failed: {restored.empty_dict} ({type(restored.empty_dict)})"
	if not isinstance(restored.empty_list, list) or len(restored.empty_list) != 0:
		return False, f"Empty list failed: {restored.empty_list} ({type(restored.empty_list)})"
	if not isinstance(restored.empty_counter, collections.Counter) or len(restored.empty_counter) != 0:
		return False, f"Empty Counter failed: {restored.empty_counter} ({type(restored.empty_counter)})"
	if not isinstance(restored.empty_defaultdict, collections.defaultdict) or len(restored.empty_defaultdict) != 0:
		return False, f"Empty defaultdict failed: {restored.empty_defaultdict} ({type(restored.empty_defaultdict)})"

	return True, "Empty collections round-tripped with exact types"


_ok, _detail = _test_empty_collections_round_trip()
check("Empty collections preserve runtime types", _ok, _detail)


def _test_variable_length_tuple_round_trip():
	"""Verify variable-length Tuple[T, ...] round-trips correctly."""
	@dataclass
	class TupleProbe:
		var_ints: Tuple[int, ...] = (10, 20, 30, 40)
		empty_tuple: Tuple[str, ...] = ()

	orig = TupleProbe()
	blob = serialize_state(orig)
	restored = deserialize_state(blob, target_type=TupleProbe)

	if not isinstance(restored.var_ints, tuple) or restored.var_ints != (10, 20, 30, 40):
		return False, f"Variable tuple failed: {restored.var_ints}"
	if not isinstance(restored.empty_tuple, tuple) or restored.empty_tuple != ():
		return False, f"Empty tuple failed: {restored.empty_tuple}"

	return True, "Variable length tuples round-tripped with exact types"


_ok, _detail = _test_variable_length_tuple_round_trip()
check("Variable-length tuples round-trip", _ok, _detail)


def _test_nested_composite_structures():
	"""Verify nested composite structures (e.g. List[Set[str]], Dict[str, List[int]])."""
	@dataclass
	class CompositeProbe:
		sets_in_list: List[Set[str]] = field(default_factory=lambda: [{"a", "b"}, {"c"}])
		lists_in_dict: Dict[str, List[int]] = field(default_factory=lambda: {"key1": [1, 2], "key2": [3, 4]})

	orig = CompositeProbe()
	blob = serialize_state(orig)
	restored = deserialize_state(blob, target_type=CompositeProbe)

	if not isinstance(restored.sets_in_list, list) or len(restored.sets_in_list) != 2:
		return False, f"sets_in_list failed: {restored.sets_in_list}"
	if not isinstance(restored.sets_in_list[0], set) or restored.sets_in_list[0] != {"a", "b"}:
		return False, f"Nested set failed: {restored.sets_in_list[0]}"
	if not isinstance(restored.lists_in_dict, dict) or restored.lists_in_dict.get("key1") != [1, 2]:
		return False, f"lists_in_dict failed: {restored.lists_in_dict}"

	return True, "Nested composite structures round-tripped correctly"


_ok, _detail = _test_nested_composite_structures()
check("Nested composite structures round-trip", _ok, _detail)


def _test_unregistered_defaultdict_and_counter_field():
	"""Verify newly declared Counter and defaultdict fields on state dataclasses reconstruct correctly."""
	@dataclass
	class ExtendedProjectsState(HouseholdState):
		extra_counter: collections.Counter = field(default_factory=lambda: collections.Counter({"copper": 10}))
		extra_defaults: DefaultDict[str, int] = field(default_factory=lambda: collections.defaultdict(int, {"gold": 5}))

	orig = ExtendedProjectsState(capital=50.0)
	blob = serialize_state(orig)
	restored = deserialize_state(blob, target_type=ExtendedProjectsState)

	if not isinstance(restored.extra_counter, collections.Counter):
		return False, f"Unregistered Counter is not Counter: {type(restored.extra_counter)}"
	if restored.extra_counter.get("copper") != 10:
		return False, f"Counter value mismatch: {restored.extra_counter}"
	if not isinstance(restored.extra_defaults, collections.defaultdict):
		return False, f"Unregistered defaultdict is not defaultdict: {type(restored.extra_defaults)}"
	if restored.extra_defaults["unknown_key"] != 0:
		return False, f"Default factory failed on unregistered defaultdict: {restored.extra_defaults['unknown_key']}"

	return True, "Unregistered Counter and defaultdict fields reconstructed automatically"


_ok, _detail = _test_unregistered_defaultdict_and_counter_field()
check("Unregistered Counter and defaultdict fields reconstructed", _ok, _detail)


def _test_optional_type_variations():
	"""Verify Optional fields behave properly both when None and when holding complex values."""
	@dataclass
	class OptionalProbe:
		opt_dict: Optional[Dict[str, float]] = None
		opt_set: Optional[Set[int]] = None
		opt_proj: Optional[ActiveProjectState] = None

	# Case A: all None
	orig_none = OptionalProbe()
	blob_none = serialize_state(orig_none)
	restored_none = deserialize_state(blob_none, target_type=OptionalProbe)
	if restored_none.opt_dict is not None or restored_none.opt_set is not None or restored_none.opt_proj is not None:
		return False, f"Expected None for all fields, got: {restored_none}"

	# Case B: all populated
	orig_populated = OptionalProbe(
		opt_dict={"ratio": 0.75},
		opt_set={7, 14},
		opt_proj=ActiveProjectState(ph_left=12.0)
	)
	blob_populated = serialize_state(orig_populated)
	restored_populated = deserialize_state(blob_populated, target_type=OptionalProbe)

	if not isinstance(restored_populated.opt_dict, dict) or restored_populated.opt_dict != {"ratio": 0.75}:
		return False, f"Populated opt_dict failed: {restored_populated.opt_dict}"
	if not isinstance(restored_populated.opt_set, set) or restored_populated.opt_set != {7, 14}:
		return False, f"Populated opt_set failed: {restored_populated.opt_set}"
	if not isinstance(restored_populated.opt_proj, ActiveProjectState) or restored_populated.opt_proj.ph_left != 12.0:
		return False, f"Populated opt_proj failed: {restored_populated.opt_proj}"

	return True, "Optional type variations verified"


_ok, _detail = _test_optional_type_variations()
check("Optional field variations round-trip", _ok, _detail)

