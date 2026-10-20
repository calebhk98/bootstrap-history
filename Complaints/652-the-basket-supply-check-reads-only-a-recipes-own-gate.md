# The basket supply check reads only a recipe's own gate, not its inputs' gates

**Status:** open

Found closing 618. `validate`'s check that a start can supply its households' basket goods reads each good's recipe
gate but not the gates of the recipe's inputs. Mexica holds `mat_bronze`, so bronze looked suppliable, but its input
`tin_kg` is gated on a node Mexica does not hold and no partner trades it, so no implement metal could be made there.

What it would take: the check walks a good's whole input closure under the start's held nodes and reachable partners,
and reports a basket good with no complete chain. Test: a built recipe set where a good's own gate is held and an
input's is not is reported unsuppliable.
