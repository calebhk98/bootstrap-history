"""Signatures of the kernels that no hand-built fixture year reaches, so `compile-kernels` compiles them from types.

A kernel the fixture economy steps through needs no entry here: `compile-kernels` runs the fixture and numba compiles
what it reaches. A kernel that only a full civilisation reaches (or only a rare branch) is listed with the numba types
its caller passes: a different dtype or layout compiles a second version the game never calls, so these follow the
callers. `test_compile_kernels` fails when a registered kernel is reached by neither."""


def declared_signatures():
    """{`module.function`: [argument-type tuple, ...]} using numba types; imported lazily so plain Python works."""
    from numba import types
    number = types.float64
    integer = types.int64
    flag = types.boolean

    def array(element, dimensions):
        return types.Array(element, dimensions, "C")

    return {
        "sim.economy.merchants_kernel.lost_share": [(number, integer)],
        "sim.economy.merchants_kernel.search_good": [(
            array(number, 1), array(number, 2), array(integer, 2), array(integer, 1), array(flag, 1),
            number, number, number, number, number)],
        "sim.geography.routes_tree_kernel.least_tree": [(
            array(integer, 1), array(integer, 1), array(number, 1), array(number, 1), array(integer, 1),
            array(number, 1), array(number, 1), flag)],
        "sim.labour.market.sold_hours_kernel.sold_hours": [(number, array(number, 2), number)],
        "sim.labour.market.training_kernel.age_cohorts": [(
            array(integer, 1), array(number, 1), array(number, 1), array(number, 2), integer, integer, array(number, 1), array(flag, 1),
            integer, array(number, 1), number, number, array(number, 2), array(flag, 1), array(integer, 1), array(integer, 1),
            array(flag, 1), array(integer, 1), array(integer, 1), array(number, 1), array(flag, 1), array(flag, 1))],
    }
