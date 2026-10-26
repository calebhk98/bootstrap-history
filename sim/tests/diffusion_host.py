"""The diffusion module over plain values for the tests of what a society needs first."""
from sim.diffusion.module import Diffusion
from sim.tests import module_harness


def gated(civilisation, done=(), stock_met=False):
    """The diffusion module of a society described by `civilisation` that has finished the nodes `done`; holding the
    stock a gate asks for is `stock_met`."""
    return module_harness.build(Diffusion, views={
        "civilisation": civilisation, "techniques_held": set(done), "stock_holds_met": lambda stock: stock_met})
