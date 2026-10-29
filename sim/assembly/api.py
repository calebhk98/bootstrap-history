"""The assembly package's only door: modules, mods and the engine import from here and nowhere else."""

WALL = "two-way"  # nothing here imports sim/engine/ or another package

from .assemble import Assembly, assemble
from .clock import Clock
from .describe import dependency_lines, record
from .kernels import Kernel, Sample
from .framework import FRAMEWORK_ID
from .errors import AssemblyError, StaleView, ViewWrite
from .module import Module
from .needs import Needs, Point
from .spec import FIRST, KEYED, LIST, QUOTE, SUM, TABLE, Command, ExtensionPoint, ModuleSpec, Operations, PhaseHook, Provision, ViewSpec
from .views import View
from .slots import SEAT, WORLD, bind_seat, bind_world, new_slots, notify_seat_bound, rebind, revive_slots
