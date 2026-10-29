"""Mod Python code: run only for a mod the player has allowed, and only the exact files they allowed.

A mod lists files in its manifest `code` and declares `"permissions": ["code"]`. `simulator.py mod-allow <id>` prints
the files and writes their sha256 digests to `mods/consent.json`; a mod whose files are not all listed there with the
same digests is skipped (a changed file needs consent again). An allowed file is run with its `register(api)`
function, handed a `ModCodeApi`: the one door to commands, actor kinds, policies and spawners, every name forced into
the mod's `<mod_id>:` namespace.

This is NOT a sandbox. Python in this process has the player's full permissions (files, network, credentials), and no
in-process restriction of CPython holds against a hostile author. The consent file is the protection: allow code only
from an author you trust. A real boundary needs a subprocess or WASM host with an allowlisted message API.
"""
import hashlib
import json
import os
import random
import sys
import types
from typing import Any, Callable, Dict, List, Optional, Tuple

from sim.assembly.api import ModAccess, NeedsAccess, Operations
from sim.interface.api import CODE, CommandDeclaration, FigureDeclaration
from sim.stores.api import ModStore, StoreSpec, WriteStore, check_spec

from sim.content.api import get_ordered_mods
from sim.content.api import ModError, ModManifest
from sim.content.api import SEPARATOR

CONSENT_FILE = "consent.json"
CODE_PERMISSION = "code"

LOADED: Dict[str, str] = {}      # mod id -> "ran" or the reason it did not
# (mods directory, mod id) -> what that mod's `register(api)` asked of the assembly (sim.assembly Operations: modules added,
# replaced, removed or extended, answers provided, year phases). Data only: a game applies the ones of its own mod set.
MOD_OPERATIONS: Dict[Tuple[str, str], Operations] = {}


def code_files(manifest: ModManifest) -> Dict[str, str]:
    """{relative name: absolute path} of the code files the manifest lists, checked to lie inside the mod."""
    base = os.path.realpath(manifest.directory)
    found = {}
    for name in manifest.code:
        path = os.path.realpath(os.path.join(base, name))
        if not path.startswith(base + os.sep) or not name.endswith(".py") or not os.path.isfile(path):
            raise ModError("mod %s lists code file %r which is not a .py file inside the mod" % (manifest.id, name))
        found[name] = path
    return found


def file_digests(manifest: ModManifest) -> Dict[str, str]:
    digests = {}
    for name, path in sorted(code_files(manifest).items()):
        with open(path, "rb") as source:
            digests[name] = hashlib.sha256(source.read()).hexdigest()
    return digests


def read_consent(mods_dir: str) -> Dict[str, Dict[str, str]]:
    path = os.path.join(mods_dir, CONSENT_FILE)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as source:
        return json.load(source)


def is_allowed(mods_dir: str, manifest: ModManifest) -> bool:
    return read_consent(mods_dir).get(manifest.id) == file_digests(manifest)


def allow(mods_dir: str, mod_id: str) -> Dict[str, str]:
    """Record consent to the mod's current code files; returns the digests written."""
    manifest = next((found for found in get_ordered_mods(mods_dir) if found.id == mod_id), None)
    if manifest is None or not manifest.code:
        raise ModError("mod %s is not installed or ships no code" % mod_id)
    consent = read_consent(mods_dir)
    consent[mod_id] = file_digests(manifest)
    with open(os.path.join(mods_dir, CONSENT_FILE), "w", encoding="utf-8") as target:
        json.dump(consent, target, indent=1, sort_keys=True)
        target.write("\n")
    return consent[mod_id]


def code_report(mods_dir: str) -> List[str]:
    """One line per code-shipping mod: whether it is allowed and which files it would run."""
    lines = []
    for manifest in get_ordered_mods(mods_dir):
        if manifest.code:
            state = "allowed" if is_allowed(mods_dir, manifest) else "NOT allowed (not run; `mod-allow %s` to allow)" % manifest.id
            lines.append("mod %s ships code %s: %s" % (manifest.id, ", ".join(manifest.code), state))
    return lines


class ModCodeApi:
    """What a mod's `register(api)` may call. Every name it creates is `<mod_id>:<name>`."""

    def __init__(self, mod_id: str):
        self.mod_id = mod_id
        self.operations = Operations(mod_id)

    def reads(self, *views: str) -> None:
        """Declare the published views the mod's code reads. Its commands, phases, figures and providers are handed a
        `ModAccess` that answers `access.view(name)` for these only; any other view is refused naming this mod and the view."""
        self.operations.reads = self.operations.reads + tuple(name for name in views if name not in self.operations.reads)

    def sends(self, *commands: type) -> None:
        """Declare the command classes the mod's code sends with `access.send(command)`; any other is refused naming this mod."""
        self.operations.sends = self.operations.sends + tuple(kind for kind in commands if kind not in self.operations.sends)

    def access_of(self, game: Any) -> ModAccess:
        """What the mod's code is handed in place of `game` (a command, phase or figure is called with the game)."""
        return game.assembly.mod_access[self.mod_id]

    def with_access(self, handler: Callable) -> Callable:
        """`handler(access, *arguments)` as the engine calls it: with the game first."""
        return lambda game, *arguments, **keywords: handler(self.access_of(game), *arguments, **keywords)

    def add_module(self, spec: Any) -> None:
        """A new module (sim/assembly): its id is `<mod_id>:<name>`, with its own state, views, commands and phases."""
        self.operations.added = self.operations.added + (spec,)

    def replace_module(self, module_id: str, spec: Any) -> None:
        """Stand in for a module: the spec must publish every view and apply every command the replaced one did."""
        self.operations.replaced[module_id] = spec

    def remove_module(self, module_id: str) -> None:
        """Take a module out; refused while any remaining module reads one of its views or sends it a command."""
        self.operations.removed = self.operations.removed + (module_id,)

    def extend_module(self, module_id: str, layer: type) -> None:
        """A class laid over the module's implementation: its methods override, `super()` reaches the layer below."""
        self.operations.layers[module_id] = self.operations.layers.get(module_id, ()) + (layer,)

    def adjust_view(self, view: str, function: Callable, reads: Any = ()) -> None:
        """`function(access, value, *key_or_arguments) -> value` over a published view; `access.view(name)` answers the views in
        `reads` and refuses any other, naming this mod; an adjuster sends nothing."""
        entry = (function, tuple(reads))
        self.operations.adjusters[view] = self.operations.adjusters.get(view, ()) + (entry,)

    def withdraw(self, provision: str) -> None:
        """Take a shipped module's answer out of an extension point, by its `<module_id>.<name>`."""
        self.operations.withdrawn = self.operations.withdrawn + (provision,)

    def provide(self, point: str, function: Callable) -> None:
        """Add an answer to a module's extension point."""
        self.operations.provided[point] = self.operations.provided.get(point, ()) + (function,)

    def kernel(self, name: str, function: Callable) -> None:
        """Replace the engine's computation `<module_id>.<name>` with `function`, which must
        take the reference's arguments and answer what it answers on the kernel's stored samples, exactly or within the
        kernel's declared tolerance; the game is refused, naming this mod and the kernel, when it does not."""
        if name in self.operations.kernels:
            raise ModError("mod %s replaces the kernel %s twice" % (self.mod_id, name))
        self.operations.kernels[name] = function

    def qualified(self, name: str) -> str:
        return name if name.startswith(self.mod_id + SEPARATOR) else self.mod_id + SEPARATOR + name

    def command(self, name: str, **fields: Any) -> Callable:
        """Decorator for a handler `(access, nodes, cmd, ended) -> dict`; fields as in sim/ui/proto/command_registry.py
        (group, summary, usage and description are required). Offered to the interface module's `interface_commands` point."""
        missing = [required for required in ("group", "summary", "usage", "description") if required not in fields]
        if missing:
            raise ModError("mod %s: command %s needs %s" % (self.mod_id, name, ", ".join(missing)))

        def decorate(handler: Callable) -> Callable:
            declaration = CommandDeclaration(self.mod_id, self.qualified(name), CODE,
                                             dict(fields, aliases=list(fields.get("aliases", ()))), self.with_access(handler))
            self.provide("interface_commands", lambda: [declaration])
            return handler
        return decorate

    def figure(self, name: str, label: str, unit: str = "", digits: int = 1, since: Optional[Callable] = None) -> Callable:
        """Decorator for `compute(access) -> {"value", "components", "flows", "drivers"}` (sim/ui/figures.py): a headline figure
        that explains its own change. Offered to the interface module's `interface_figures` point."""
        def decorate(compute: Callable) -> Callable:
            declaration = FigureDeclaration(self.mod_id, self.qualified(name), label, unit, digits, self.with_access(compute),
                                            None if since is None else self.with_access(since))
            self.provide("interface_figures", lambda: [declaration])
            return compute
        return decorate

    def actor_kind(self, kind: str, actor_class: Any) -> None:
        """A new kind of actor: records of the kind build `actor_class` objects (the actors module's `actor_kinds` point)."""
        answer = {self.qualified(kind): actor_class}
        self.provide("actor_kinds", lambda: answer)

    def policy(self, kind: str, factory: Callable) -> None:
        """A policy nameable from a save file: `factory()` makes it (the actors module's `actor_policies` point)."""
        answer = {self.qualified(kind): factory}
        self.provide("actor_policies", lambda: answer)

    def spawner(self, name: str, function: Callable) -> None:
        """A rule run every year after the actors' turns: `function(registry, world) -> ids of the actors it founded`."""
        answer = [(self.qualified(name), function)]
        self.provide("actor_spawners", lambda: answer)

    def player_command(self, name: str, handler: Callable) -> None:
        """An order a player actor can queue as `{"command": name, ...}`: `handler(player, order, world) -> detail text`,
        refusing by raising `CommandRejected` (the actors module's `player_commands` point)."""
        answer = {self.qualified(name): handler}
        self.provide("player_commands", lambda: answer)

    def director_overhead(self, function: Callable) -> Callable:
        """Charge `function(access) -> hours` against the directed-hours pool (management layers, say). The hours count as
        committed, so every free-hours check sees them; a negative answer counts as zero (the workforce module's
        `director_overhead` point)."""
        self.provide("director_overhead", NeedsAccess(function))
        return function

    def phase(self, name: str, scope: str, handler: Callable, after: Any = (), before: Any = ()) -> None:
        """A step in the year: `scope` is "seat" (`handler(access, seat_id)`, once per seat) or "world" (`handler(access, seats)`,
        once). Placed right after its latest `after` and/or right before its earliest `before`; each names a shipped
        phase (see sim/engine/year_phases.py) or another mod's `<mod_id>:<name>`. At least one is required."""
        from .year_phases import SEAT, WORLD, Phase
        after, before = [after] if isinstance(after, str) else list(after), [before] if isinstance(before, str) else list(before)
        if scope not in (SEAT, WORLD) or not (after or before):
            raise ModError("mod %s phase %s needs scope 'seat' or 'world' and an 'after' or 'before'" % (self.mod_id, name))
        phase = Phase(self.qualified(name), scope, self.with_access(handler), self.mod_id, tuple(self.phase_reference(n) for n in after),
                      tuple(self.phase_reference(n) for n in before))
        self.operations.phases = self.operations.phases + (phase,)

    def phase_reference(self, name: str) -> str:
        from .year_phases import SHIPPED
        return name if name in {phase.name for phase in SHIPPED} or SEPARATOR in name else self.qualified(name)

    def store(self, name: str, keyed_by: str, default: Any, unit: str = "") -> Any:
        """Declare a saved value per "tile", "actor" or "actor_pair" (an ordered pair); returns a handle with
        `get(access, key)`, `set(access, key, value)` and `items(access)`. Figures and `read` commands reach it as
        `stores.<mod_id>:<name>.<key>`, and `map` shows a tile store as a layer. A name is declared once across mods."""
        spec = StoreSpec(self.qualified(name), self.mod_id, keyed_by, default, unit)
        check_spec(spec, "mod %s" % self.mod_id)
        self.provide("store_declarations", lambda: [spec])
        self.reads("store")
        self.sends(WriteStore)
        return ModStore(spec, self.mod_id)

    def write_store(self, access: Any, name: str, key: Any, value: Any) -> None:
        """Write a value to one of this mod's declared stores; an undeclared store is an error naming the mod."""
        self.effects.write_store(access, self.qualified(name), key, value)

    @property
    def effects(self) -> Any:
        """The supported ways to change the world (sim/engine/mod_effects.py): `pay`, `pay_edge`, `receive_from_edge`,
        `add_goods`, `remove_goods`, `kill_people`, `move_people`, `transfer_tile`, `write_store`, `record_event`. Each is called
        with the mod's access and sends the owner's command, so the mod declares it (`uses_effects`, or `reads` and `sends`)."""
        from .mod_effects import ModEffects
        return ModEffects(self.mod_id)

    def uses_effects(self, *names: str) -> None:
        """Declare the views and commands the named `effects` operations use (`EFFECT_NEEDS` in sim/engine/mod_effects.py)."""
        from .mod_effects import EFFECT_NEEDS
        unknown = [name for name in names if name not in EFFECT_NEEDS]
        if unknown:
            raise ModError("mod %s uses effects %s, which are not among %s" % (self.mod_id, ", ".join(unknown), ", ".join(sorted(EFFECT_NEEDS))))
        for name in names:
            views, commands = EFFECT_NEEDS[name]
            self.reads(*views)
            self.sends(*commands)

    def town_provider(self, name: str, function: Callable, mortality_premium: Optional[Callable] = None) -> None:
        """Say how many people live in a tile's town: `function(access, tile, nominal_people) -> people or None`. The
        optional `mortality_premium(access, tile, town_people) -> share of the baseline death rate or None` is the
        town's excess mortality, which reaches `Population.step`."""
        self.provide("town_population", NeedsAccess(function))
        if mortality_premium is not None:
            self.provide("town_mortality_premium", NeedsAccess(mortality_premium))

    def externality(self, provider: Callable) -> None:
        """Feed harm into the year: `(access, year) -> {"deaths_by_band": {...}, "yield_factor_by_tile": {...}}` (either key
        optional). The deaths join the year's epidemic deaths; the factors multiply the yield of land-bound producers on a tile
        (the demography module's `externality` point)."""
        self.provide("externality", NeedsAccess(provider))

    def wealth_claims(self, owed: Callable, seize: Callable) -> None:
        """Register claims on other actors that a state's confiscation counts: `owed(access) -> amount` is what the acting
        household could be made to pay from them, `seize(access, amount, taker) -> amount taken` takes it for the `taker`
        (the polity module's `wealth_claims` point)."""
        self.provide("wealth_claims", NeedsAccess(lambda access: (lambda: owed(access), lambda amount, taker: seize(access, amount, taker))))

    @staticmethod
    def rng(world: Any, *parts: Any) -> random.Random:
        """The world's keyed random source, so saves and the fingerprint stay reproducible."""
        return world.rng_for(*parts)


def operations_of(mods_dir: str) -> List[Operations]:
    """What the mods of `mods_dir` that ran asked of the assembly, in mod load order."""
    directory = os.path.realpath(mods_dir)
    return [MOD_OPERATIONS[(directory, manifest.id)] for manifest in get_ordered_mods(mods_dir) if (directory, manifest.id) in MOD_OPERATIONS]


def run_mod_code(mods_dir: str, make_api: Callable[[str], ModCodeApi] = ModCodeApi) -> Dict[str, str]:
    """Run each allowed code-shipping mod once per process, keeping what it asked of the assembly (`operations_of`); skipped
    mods are named with the reason. Nothing global is changed: a game applies the operations of its own mod set."""
    directory = os.path.realpath(mods_dir)
    for manifest in get_ordered_mods(mods_dir):
        key = (directory, manifest.id)
        if not manifest.code or (LOADED.get(manifest.id) == "ran" and key in MOD_OPERATIONS):
            continue
        if not is_allowed(mods_dir, manifest):
            LOADED[manifest.id] = "no consent"
            MOD_OPERATIONS.pop(key, None)
            continue
        api = make_api(manifest.id)
        for name, path in code_files(manifest).items():
            with open(path, "rb") as source:
                code = compile(source.read(), path, "exec")
            module = types.ModuleType("sim_mod.%s.%s" % (manifest.id, os.path.splitext(os.path.basename(name))[0]))
            module.__file__ = path
            previous = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                exec(code, module.__dict__)   # consented code; see the module docstring for the boundary
            finally:
                sys.dont_write_bytecode = previous
            register: Optional[Callable] = getattr(module, "register", None)
            if not callable(register):
                raise ModError("mod %s: %s defines no register(api) function" % (manifest.id, name))
            register(api)
        MOD_OPERATIONS[key] = api.operations
        LOADED[manifest.id] = "ran"
    from .year_phases import ordered_phases
    ordered_phases([phase for operations in operations_of(mods_dir) for phase in operations.phases])   # a bad phase constraint is a load error
    return dict(LOADED)
