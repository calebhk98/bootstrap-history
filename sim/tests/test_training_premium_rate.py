"""The training premium and the career annuity at a discount rate of zero. Functions called on written-out numbers."""
QUICK_TOPIC = True

import math

from .harness import *  # noqa: F401,F403
from sim.labour.market.premium import annuity_factor, training_premium

check("no training needs no premium at any rate", training_premium(0.0, 0.0, 40.0) == 1.0 == training_premium(0.0, 0.05, 40.0))
check("at a zero rate the premium is the career over the years after training",
      abs(training_premium(10.0, 0.0, 40.0) - 40.0 / 30.0) < 1e-9, training_premium(10.0, 0.0, 40.0))
near_zero = training_premium(10.0, 1e-9, 40.0)
check("...and is the limit of the premium as the rate falls to zero", abs(near_zero - 40.0 / 30.0) < 1e-6, near_zero)
check("a positive rate raises the premium above the undiscounted one", training_premium(10.0, 0.05, 40.0) > 40.0 / 30.0)
check("an annuity at a zero rate is the years", annuity_factor(0.0, 7.0) == 7.0)
check("an annuity of no years is nothing", annuity_factor(0.05, 0.0) == 0.0)
check("a discounted annuity is the continuous present value",
      abs(annuity_factor(0.05, 20.0) - (1.0 - math.exp(-1.0)) / 0.05) < 1e-9)
