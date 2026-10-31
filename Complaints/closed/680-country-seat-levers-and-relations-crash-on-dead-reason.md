# Levers and relations sent as a country seat crash on the missing founder

**Status:** closed - the dead_reason read no longer exists on main; the country-seat join itself failed (SetSeatHolder undeclared in the seats module sends), now declared and tested

Found while recording the protocol golden transcripts (`sim/tests/protocol_golden/README.md`). After `join` with
`seat_kind: country`, sending `levers`, `lever` or `relations` with `"as"` that seat answers
`internal error ... AttributeError: 'NoneType' object has no attribute 'dead_reason'`; `join` and `seats` work. A
country seat has no founder (`state_seat.seat_from_template`, `COUNTRY_SEAT`), so `state.founder` is `None` while
it acts, and something on those commands' path reads `state.founder.dead_reason` without asking whether the seat
holds a founder. It reproduces in a subprocess as well as in process.

What would fix it: find the read (the traceback names it), make it ask the seat's kind, and add a regression test
that sends each of the three commands as a country seat. The golden transcripts leave country seats out so the fix
does not move them; add a country-seat script once it is fixed.
