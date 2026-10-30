"""The engine, split by subject.

The split is about where you look to find something; it changes nothing
about what the model does.

    data       loading the tree, prices, geography and civilisations
    geography  where things are, and what that costs to reach
    economy    money, materials, and the works that consume both
    labour     people: hiring, teaching, buying, paying
    society    what a society believes, and what it does to you for being large
    fog        what the player can see, and what their work risks losing
    projects   starting, stopping, finishing and abandoning a piece of work
    core       the Sim class: one year, and the loop over years
    protocol   the JSON a player or an agent speaks
    cli        the command line

The six subject modules are mixins rather than separate objects. That is a
deliberate compromise: Sim's state is one interlocking thing - revenue depends
on staff, staff on money, money on hazards, hazards on what you have built -
and pretending otherwise by handing each module its own object would have meant
threading the same state through in pieces. The mixin lets each subject live in
its own file without inventing boundaries the model does not have.

The facts the root states on itself (`year`, `civ`, `done`, ...) are declared in `core.py` through
root_facts.py, not by a mixin. The year's
steps the root runs itself are plain functions in year_steps.py and the seat
registry's are in seat_registry.py, so `core.py` holds the class and a
one-line method for each. See `sim/ARCHITECTURE.md` for the current base list and the script
that derives it.

Enter through simulator.py, which is what every note, test and instruction in
this project refers to.
"""
