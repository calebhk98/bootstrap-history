# A field that means something by not being there

`sim/engine/actors/household.py` says this about itself, in its own class
docstring:

    A NOTE ON WHAT IS *ABSENT* HERE, NOT JUST WHAT IS SET: several fields
    below are deliberately never assigned in `__init__` at all, and are
    created lazily, the first time some method does
    `getattr(self.household, "name", default)`.
    ...
    A save file missing one of these fields means "this has never happened
    yet", not "zero"

Eight fields work this way. The file names them:

    insolvent_years, wage_hours_this_year, _said_deputies, _said_scandal,
    last_withdrawal, _said_near_limit, _said_autoopen, _said_parallelism

They are the members of `SAVE_FIELDS` (`sim/engine/proto/saveload.py`) for
which absence is load-bearing, and the constructor deliberately leaves them
out, while the seven trackers listed immediately below them in the same
constructor DO get real starting values, precisely because they are not in
`SAVE_FIELDS`.

**This is bad practice and should not be how the distinction is carried.**
The stakeholder's own words: "It should be created, and saved as null, not
check if it exists."

## Why it is bad, stated precisely

The information "this has never happened yet" is real and worth keeping. The
objection is to the channel it travels through, which is the presence or
absence of an attribute. That channel has four properties nobody chose:

1. **It is invisible at the definition site.** A reader of `__init__` sees
   what is set. Nothing there says "and eight more fields exist, sometimes".
   The only record is a prose comment, which is why the comment had to be
   written at that length.
2. **The reader cannot tell a deliberate omission from a missed one.** Both
   look like nothing. The file's own comment says the eight "have been
   checked against `SAVE_FIELDS`", which is a check somebody did once, by
   hand, and which nothing re-runs.
3. **Every read site has to spell the default the same way.** The value is
   reconstructed through `getattr(obj, name, default)` at every call site,
   and nothing checks that the twenty-three sites agree on what the default
   is. One site defaulting to `0` where another defaults to `None` is a
   disagreement about whether the thing has happened, and it is invisible.
   Speed is not the argument. Builtin `getattr` costs about 25ns against
   8ns for a direct attribute read, and every getattr call in the engine
   together is 1.4% of a 60-year run - 0.049s of 3.608s over 418,703 calls:

       python3 -m cProfile -s cumtime sim/simulator.py run --horizon 60 --mc 1 --seed 1

   and read the `builtins.getattr` row. The 50x figure that gets quoted for
   getattr is a class defining `__getattr__` and paying a Python-level
   dispatch on every miss; no class in `sim/` defines one
   (`grep -rn "def __getattr__" sim/`).
4. **A correct-looking change breaks it silently.** The constructor's comment
   records exactly this: promoting one of these to a real `__init__`
   attribute "passed the whole test suite while silently breaking save-file
   semantics", and broke year 0's hash on all nine reference scenarios. The
   suite could not see it. `perf_fingerprint.py` could.

Point 4 is the one that makes this a complaint rather than a style note. The
invariant is enforced by a comment and by one tool that has to be run
deliberately.

## The fix the stakeholder named, and why it is available here

Initialise all eight in `__init__` to `None`, save `None`, and replace each
`getattr(household, name, default)` with an explicit `is None` test.

`None` carries the same meaning the absence carries, in a place a reader can
see, with a type that says it. `Optional[int]` in the annotation states the
invariant where the field is defined rather than in a paragraph above it.

The thing that normally blocks this kind of change does not apply.
CLAUDE.md §3.5 is unusually emphatic that this project has no save-format
migration, ever: "rename a persisted field, drop one, change its units,
restructure the whole save. No shim, no version stamp, no upgrade path, no
`if "old_key" in data`." A save written by an old build does not have to load
in a new one. So the usual reason to preserve an absence-means-something
encoding, that old saves are already written that way, is explicitly not a
reason here.

## What the change would actually cost, so nobody underestimates it

Two things, both real:

**`perf_fingerprint.py` will report all nine scenarios changed, and that is
expected rather than a failure.** The fingerprint hashes `SAVE_FIELDS`, and a
field serialised as `null` is not the same bytes as a field that is absent.
The simulated behaviour would be unchanged; the save's shape would not be.
That means the usual proof instrument cannot be used in its usual way for
this change, and something else has to carry the argument, most likely a
temporary check that the two encodings decode to identical behaviour at every
read site before the old encoding is removed. Whoever does this should decide
that up front, because "the fingerprint differs" will otherwise look like a
bug for the whole of the work.

**Every read site has to be found and converted together, and there are 23
of them.** The eight fields are read through `getattr(owner, "name",
default)` at exactly this many places:

    grep -rnE 'getattr\([A-Za-z_][A-Za-z0-9_.]*, *"(insolvent_years|wage_hours_this_year|_said_deputies|_said_scandal|last_withdrawal|_said_near_limit|_said_autoopen|_said_parallelism)" *,' --include=*.py sim/ | wc -l
    23

split `insolvent_years` 8, `wage_hours_this_year` 8, `last_withdrawal` 2, and
one each for the five `_said_*` flags, across eleven files
(`grep -rl` the same pattern), concentrated in `core_step_phases.py`,
`projects_starting.py` and `labour_*.py`.

Twenty-three sites is the whole cost, and it is small enough that the
conversion is an afternoon. Scope the grep to the eight field names. A grep
for every `getattr` on `self`, `sim` or `s` across `sim/engine/` answers 132
and measures something else entirely: `fog` alone accounts for 31 of those
reads and has nothing to do with this complaint.

A half-converted field is still worse than either encoding, because one site
reading absence and another reading `None` disagree about whether a thing has
happened. Convert a field's sites in one commit, not a file's.

## Not being fixed now

Explicitly deferred by the stakeholder. Filed so the decision is recorded
rather than rediscovered, and so the next person to read
`household.py`'s docstring finds a complaint number next to the paragraph
that defends the current behaviour instead of only the defence.
