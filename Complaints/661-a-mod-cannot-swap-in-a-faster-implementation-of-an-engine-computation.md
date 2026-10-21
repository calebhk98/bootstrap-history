# A mod cannot swap in a faster implementation of an engine computation

**Status:** open - owner decision 2026-10-21: wanted, lower priority than the opening (473) and year speed (497)

A mod's code can add commands, actor kinds, policies, spawners, phases of the year and three providers (towns,
externalities, harvest), and changes the world only through `api.effects` (`sim/engine/mod_code.py`, `mods/README.md`
"Mod code"). It has no way to replace how the engine computes something already in the year: the goods clearing, the
price root-finds, the merchants' route search. A speed mod (for example one using numpy, or a compiled extension)
can only do it today by overwriting a module function from `register(api)`. That is unsupported:

- it breaks silently when the patched function is renamed or split, which happens often (`min_game_version` is a
  floor, not a match);
- nothing checks the replacement gives the same answers, and a float sum in another order changes a run
  (`sim/tests/test_run_reproducibility.py` exists for that bug class);
- the functions worth replacing take `Sim` or large mutable records, so a replacement depends on the god object's
  shape rather than on a stated input and output.

Why it matters: speed mods are common in games of this kind, and the owner wants speed-ups swappable without engine
edits (CLAUDE.md 4.7's spirit: content and alternatives are data and registered code, not forks). It also pushes the
engine toward plain functions with stated inputs, which section 6 asks for anyway ("where a rule needs the whole
`Sim`, pull it into a plain function first").

What it would take:

1. Name the replaceable computations ("kernels") the engine calls through a registry, each a plain function with a
   declared input and output type that does not take `Sim`. Start with the ones 497 measures as largest.
2. `api.kernel(name, function)` in the mod interface. The engine's own version stays the default and the reference.
3. At load, the loader runs the mod's version against the reference on the kernel's stored sample inputs and refuses
   the mod, naming it and the kernel, unless the results match (exactly, or within a tolerance the kernel declares
   with its reason). Two unrelated mods replacing one kernel is an error naming both, as for overrides.
4. The active kernel replacements are part of what a game records, so a multiplayer session can refuse a mismatch.
5. A test per kernel that calls it on built inputs, so the equivalence check and the rule test are the same fixture.

The numpy probe (branch `numpy-speed-probe`, 497) is the first candidate. If numpy itself proves worth it, the base
game can import it optionally with the pure-Python version as fallback, independently of this complaint.
