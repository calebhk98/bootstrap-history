# A mod cannot swap in a faster implementation of an engine computation

**Status:** closed - kernels exist: `sim/assembly/kernels.py` (`Kernel`, owned by a module through `ModuleSpec.kernels`), `api.kernel(name, function)` in `sim/engine/mod_code.py`, and two shipped kernels chosen by profile (`markets.fetch_wage`, `markets.least_cost_tree`, declared in `sim/markets/kernels.py`)

## What was done (the five steps)

1. A kernel is a `Kernel(name, reference, inputs, output, samples, tolerance, tolerance_reason, observe)`; the owning module calls it through the function the assembly binds (`Module.kernel(name)`, handed to the economy through `EconomySetup.kernels`), never the reference. Largest by profile of `step 2` on a saved Rome game (cProfile, 65 s): the labour market's import-cost wage `ImportCosts.wage` 17.9 s (28%, now `fetch_wage`), the merchants' route search `_candidate_routes` 8.8 s, of which the carriage table's least-cost search (`_cost_tree`, now `least_cost_tree`) is the pure part; `clear_goods` 3.5 s and the price solves are each under 6% and stay as they are. The rest of 497's profile is flat.
2. Both kernels are plain functions of plain arguments (numbers, lists, lookups), moved from the old code with the same arithmetic order. Their sample calls are built in code (`fetch_wage_samples.py`, `routes_cost_tree_samples.py`), not captured from a game: a captured call would have to hold the year's hour schedules, which are closures.
3. `api.kernel` records into the mod's `Operations`; assembly runs the replacement and the reference on every sample and refuses, naming the mod and the kernel, unless every answer is equal (or within the declared tolerance; both shipped kernels are exact). Two mods replacing one kernel, or a replacement of an undeclared kernel, is an error naming the parties.
4. The active replacements are in `assembly_record` (`kernels`: name -> mod), so a save from a game with one is refused (`save_module_set`) by a game without it.
5. `test_assembly_kernels` (the framework), `test_kernel_fetch_wage` and `test_kernel_least_cost_tree` (the rule tests on the samples) are quick-tier; `test_mod_kernels_smoke` builds games over consented code mods (equal replacement accepted and called in a stepped year, wrong one refused, two mods refused, save refused).

## Limits

- `markets.least_cost_tree` is handed to the economy's carriage table only. The demography module's urban search calls the same geography function with the reference (`sim/demography/urban.py`, `route_costs`), so a replacement does not reach it; Complaint 850.
- A replacement is checked on the samples only; one equal there and different on real input is the mod's risk (`mods/README.md` names the fingerprint).


A mod's code can add commands, actor kinds, policies, spawners, phases of the year and two providers (town size and
externalities, which carry deaths and a harvest factor), and changes the world only through `api.effects` (`sim/engine/mod_code.py`, `mods/README.md`
"Mod code"). It has no way to replace how the engine computes something already in the year: the goods clearing, the
price root-finds, the merchants' route search. A speed mod (for example one using numpy, or a compiled extension)
can only do it today by overwriting a module function from `register(api)`. That is unsupported:

- it breaks silently when the patched function is renamed or split, which happens often (`min_game_version` is a
  floor, not a match);
- nothing checks the replacement gives the same answers, and a float sum in another order changes a run
  (`python3 -m sim.tests.fingerprint record before.json` then `check before.json`, under two `PYTHONHASHSEED` values, measures that bug class; Complaint 27);
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
