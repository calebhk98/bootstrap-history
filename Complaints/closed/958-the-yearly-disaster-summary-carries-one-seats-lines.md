# The yearly disaster summary carries one seat's lines

**Status:** closed - `disaster_this_year` is built per seat and the `disaster` view answers the acting seat's entry; `sim/tests/test_hazard_telling_per_seat.py` holds it

`step_dated_shocks` (sim/hazards/shocks.py) built `disaster_this_year["messages"]` from `event_log()[logged_before:]`, which is
the log of the seat acting when the phase ends, so with several seats the summary held one seat's lines (and another seat's lines
were missing or wrongly counted). It now measures each seat's log under `act_as` and keeps `{seat: {name, messages}}`; the
`disaster_this_year` view returns the acting seat's entry. The only reader (sim/ui/proto/dispatch.py) reads it under the seat it
answers, so it is unchanged.
