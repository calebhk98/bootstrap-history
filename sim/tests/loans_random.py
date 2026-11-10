"""Random loans for the tests of the loan table: a list of `Contract`s that exercises every branch of the service rule (paid in full,
paid in part, arrears, defaults, loans paid off, a last year, tied ids, pledged land)."""
import random
from typing import List

from sim.contract_record import Contract

AGENTS = ["household:%d" % number for number in range(6)] + ["producer:%d" % number for number in range(6)] + ["bank:0", "state"]
TILES = ["tile:a", "tile:b"]


def random_loans(seed: int, count: int) -> List[Contract]:
    """`count` loans, some sharing a borrower, a lender and even an id."""
    rng = random.Random(seed)
    loans = []
    for index in range(count):
        lender, borrower = rng.sample(AGENTS, 2)
        principal = rng.choice((0.0, 5.0, rng.uniform(1.0, 500.0), rng.uniform(1.0, 500.0)))
        pledged = rng.random() < 0.3
        loans.append(Contract(
            contract_id="loan:%s:%d:%s:%d" % (rng.choice(("coin", "gold")), rng.randrange(0, 3), rng.choice(("year", "working_capital")),
                                               rng.randrange(0, 12) if rng.random() < 0.2 else index),
            lender=lender, borrower=borrower, currency=rng.choice(("coin", "coin", "gold")), principal=principal,
            rate=rng.choice((0.0, rng.uniform(0.0, 0.3))), years_left=rng.choice((0.5, 1.0, 1.0, 2.0, 7.0, rng.uniform(0.5, 9.0))),
            collateral_value=rng.uniform(0.0, 300.0) if pledged else 0.0, arrears=rng.choice((0.0, 0.0, rng.uniform(0.0, 300.0))),
            issued_year=rng.randrange(0, 4), arrears_interest=rng.choice((0.0, rng.uniform(0.0, 60.0))),
            collateral_tile=rng.choice(TILES) if pledged else "", collateral_share=rng.uniform(0.0, 0.5) if pledged else 0.0))
    return loans


def random_cash(seed: int) -> dict:
    """Cash for most agents: none, a little, a lot."""
    rng = random.Random(seed)
    return {agent: rng.choice((0.0, rng.uniform(0.0, 40.0), rng.uniform(0.0, 800.0), rng.uniform(0.0, 5000.0)))
            for agent in AGENTS if rng.random() < 0.85}
