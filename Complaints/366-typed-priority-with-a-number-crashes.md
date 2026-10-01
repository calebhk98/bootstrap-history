# Typed `priority 5` crashes with an IndexError

**Status:** open

Seen while deriving typed-line parsers from the command registry (357-363 work): typing `priority 5` in the typed play mode raises an IndexError instead of a usage message or setting the priority. Reproduce in `python3 sim/simulator.py play` (typed mode). Expected: either the command accepts the form its usage documents, or a refusal that says what it wants. A regression test should type the documented forms and a malformed one.
