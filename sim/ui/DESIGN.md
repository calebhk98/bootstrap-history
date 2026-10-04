# UI design conventions

How `sim/ui/` is built and what new screens should follow. Package rules (the wall, `ui_port`) are
in `docs/architecture/PACKAGE_WALLS.md`.

## Shape

- **The JSON reply is the contract.** A command handler (`proto/dispatch*.py`) asks the engine and
  returns a plain dict; a renderer (`proto/render*.py`) turns that dict into text and never touches
  the `Sim`. A different front end (another language, a GUI) replaces only the renderers.
- **Logic stays out of renderers.** If a screen needs a number, the handler puts it in the reply.
- **What the UI remembers beyond the engine's save** (notes, extra goals, programmes) goes through
  `memory.remembered(sim, topic)`, and every save and load goes through `memory.save_state` /
  `memory.load_state`. Where it is stored is that module's business (Complaint 401).
- **No content ids.** Screens read names, currencies, goals, trades and materials from data or the
  engine. Mods add content without touching `sim/ui/`.

## Screens

- **Short by default, detail on request.** A screen leads with what needs attention, then says
  which command shows more (`state full`, `state <section>`, `help commands <group>`).
- **Never an unbounded list.** Show the top rows, then "and N more" with the exact command for the
  next page or filter. Sort deterministically so pages do not shift.
- **Every changed number can say why.** A cause list is signed parts that add up to the change,
  plus an explicit "not itemised" line for whatever the parts miss. Never rescale the parts to
  hide the remainder. Where the engine keeps exact terms (the cash book), use them; elsewhere show
  drivers, not invented shares.
- **Errors say what happened and the next command to try**, with "did you mean" for names.
- **Automation is never silent.** What a policy or programme did this year appears in that year's
  step reply.
- **Fog first.** A view that names nodes checks visibility; under fog it shows counts.

## Tests

- Prefer renderer tests on a hand-written reply dict: they build no game and run in milliseconds.
- When a handler must run on a real game, build one `sim()` per test file and reuse it.
- Run only the topics you touched (`python3 -m sim.tests --only a,b`); the full suite is for merges.
