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
from typing import Any, Callable, Dict, List, Optional

from .mods import get_ordered_mods
from .mods_base import ModError, ModManifest
from .mods_ids import SEPARATOR

CONSENT_FILE = "consent.json"
CODE_PERMISSION = "code"

# Commands that mod code registered, waiting for the command registry (sim/ui) to take them: (mod_id, name, fields, handler)
COMMAND_REGISTRATIONS: List[tuple] = []
LOADED: Dict[str, str] = {}      # mod id -> "ran" or the reason it did not


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

    def qualified(self, name: str) -> str:
        return name if name.startswith(self.mod_id + SEPARATOR) else self.mod_id + SEPARATOR + name

    def command(self, name: str, **fields: Any) -> Callable:
        """Decorator for a handler `(sim, nodes, cmd, ended) -> dict`; fields as in sim/ui/proto/command_registry.py."""
        def decorate(handler: Callable) -> Callable:
            COMMAND_REGISTRATIONS.append((self.mod_id, self.qualified(name), fields, handler))
            return handler
        return decorate

    def actor_kind(self, kind: str, actor_class: Any) -> None:
        from sim.agents.api import register_actor_kind
        register_actor_kind(self.qualified(kind), actor_class)

    def policy(self, kind: str, factory: Callable) -> None:
        from sim.agents.api import register_policy
        register_policy(self.qualified(kind), factory)

    def spawner(self, name: str, function: Callable) -> None:
        from sim.agents.api import register_spawner
        register_spawner(self.qualified(name), function)

    def state(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """The mod's own JSON dict inside a saved game: pass `sim.state.interface`."""
        return memory.setdefault("mod_state", {}).setdefault(self.mod_id, {})

    @staticmethod
    def rng(world: Any, *parts: Any) -> random.Random:
        """The world's keyed random source, so saves and the fingerprint stay reproducible."""
        return world.rng_for(*parts)


def run_mod_code(mods_dir: str, make_api: Callable[[str], ModCodeApi] = ModCodeApi) -> Dict[str, str]:
    """Run each allowed code-shipping mod once per process; skipped mods are named with the reason."""
    for manifest in get_ordered_mods(mods_dir):
        if not manifest.code or LOADED.get(manifest.id) == "ran":
            continue
        if not is_allowed(mods_dir, manifest):
            LOADED[manifest.id] = "no consent"
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
        LOADED[manifest.id] = "ran"
    return dict(LOADED)
