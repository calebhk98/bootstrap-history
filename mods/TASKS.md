# What has to be true before `mods/` works

Nobody is doing this now. It is written down because the question was asked
while the answer was fresh, and because two of the five items below are things
this project wants anyway, mods or no mods.

Each item says what is wrong, why it matters for a mod specifically, and
roughly what it would take.

---

## 1. The tree merge keeps the first definition and says nothing

**This is the blocker, and it is not hypothetical.** While adding the
production side, a recipe was written into `data/branches/01_materials.json`
for `mat_copper`, merged, and vanished. No error, no warning in the part of
the output anyone reads. The id was already defined in another of the 41
branch files, and `sim/treetool.py`'s merge keeps the first one it reaches and
moves on. The merge log does say `duplicate id ..., keeping the first` - among
3,208 other lines.

For a mod this is fatal in the quiet way. A mod that redefines an existing
node would appear to install and do nothing, and the author would have no way
to tell whether the game had rejected their work or their work was wrong.

`sim/validate_production.py` already does the right thing for the production
directory: a key defined twice is an error that names **both files**. The tree
merge should do the same, with one exception - a mod overriding a base node is
a legitimate thing to want, so the answer is probably not "error" but
"require the override to be explicit", see item 3.

Cost: small. The merge already detects the collision; it only needs to stop
treating it as noise.

---

## 2. There is no namespacing

Every id in the tree is a bare string: `mat_copper`, `cap_heat_1300`,
`rag_paper`. Two mods that both add a material called `plasteel` collide, and
so does a mod that happens to pick an id the base game already uses.

The conventional fix is a prefix per mod - `bronze_age:mat_copper` - which
means touching every id comparison in the engine, and the tree is 2,864 nodes
of them. The cheaper fix is to require mod ids to carry the mod's own prefix
and to enforce that at load rather than in the engine: a mod named
`bronze_age` may only define ids starting `bronze_age_`, except where it is
deliberately overriding a base id (item 3). That gets most of the benefit for
almost none of the work, and it is a rule rather than a refactor.

Cost: small, if done as a load-time rule. Large, if done properly.

---

## 3. Overriding needs to be explicit

A mod will want to change a base node - retune a cost, add a prerequisite,
delete a technology that does not belong in its setting. Right now the only
way to express that is to define the id again, which item 1 silently ignores.

Needed: a way for a mod to say *I am deliberately replacing this*, and for the
loader to fail if the base node it claims to replace is not there. That last
part is what stops a mod silently breaking after the base game renames
something.

Cost: small, and it is the same mechanism as item 1.

---

## 4. No manifest, so no load order and no dependencies

A mod needs to say what it is called, what it requires, and what it conflicts
with. Without that there is no defined order, and two mods that both touch the
same thing produce a result that depends on `sorted(os.listdir(...))`.

A manifest is also where a mod declares which of the base game's assumptions
it is discarding, which matters more here than in most games - see item 5.

Cost: small. A `mod.json` and a topological sort.

---

## 5. Some things are still hardcoded, and one of them is interesting

Capability rungs, trade families and goal nodes are still partly in Python
rather than data. `data/branches/00_capabilities.json` holds the rung
definitions but `TRADE_FAMILY` in `sim/engine/data.py` is a dict in the
source, and a mod adding a new kind of worker would have to edit the engine.

These are small and individually easy. The interesting one is different.

**A fantasy mod is not a data problem.** A prehistoric tree or a sci-fi tree
is, genuinely, just more `data/branches/` files plus a civilisation - the
engine would run them today if items 1 to 4 were done. Dragons are not,
because this simulator's whole claim is that costs fall out of physical
structure. A dragon needs a calorie budget, a growth curve, a diet that
competes with humans for the same livestock, and a reason it does not simply
eat the economy. That is a modelling question, and the honest answer to
someone who wants one is that the machinery to do it properly is the same
machinery the base game needs for draft animals and has not built yet.

Which is the encouraging version of the answer: the work that makes dragons
possible is work this project is doing anyway.

---

## What this would NOT require

Worth stating, because it is the part people assume is hardest.

- **No save-format work.** CLAUDE.md 3.5: there is no save migration, ever.
  A mod changing the save shape is fine.
- **No engine rewrite for new content.** The engine reads data. A civilisation
  is a JSON file. There is no `if Rome:` anywhere.
- **No new merge machinery for production recipes.** `data/production/`
  already merges by key across files, already errors on a duplicate naming
  both sides, and already has a schema document. It was built that way so
  several authors could work at once, and a mod is just another author.

---

## Rough order, if it is ever picked up

1 and 3 together (same mechanism, and 1 is a real bug today), then 4, then 2,
then 5 as needed. Items 1 and 5's `TRADE_FAMILY` are worth doing regardless of
whether anyone ever writes a mod.
