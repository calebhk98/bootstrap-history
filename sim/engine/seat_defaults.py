"""The standing policy a new seat starts with: which automatic behaviours are on."""
from typing import Any, Dict


def default_policy(manual: bool) -> Dict[str, Any]:
    """Every automatic behaviour, on for the optimizer and off for a player who plays by hand."""
    return {
        "auto_hire":     not manual,   # grow the staff toward what you can support
        # ON for the optimizer, OFF for a player: automatically buying
        # people on a player's behalf, in a game they are playing by
        # hand, with no prompt and no line in the log, is not modelling
        # slavery, it is lying to the player about what is in their
        # household. An unattended optimizer run that says "bought 6
        # people for the workshop" in its log models the thing honestly.
        "auto_buy_people": not manual,
        "auto_manumit":  not manual,
        "auto_train":    not manual,   # teach trades this society does not have
        "auto_mine":     not manual,   # sink shafts when a material binds
        "auto_forest":   not manual,   # buy coppice when charcoal binds
        "auto_mothball": True,         # stop working what you cannot pay for
        # OFF FOR A PLAYER, like every other automation, and on for the
        # optimizer, which the long civilisation runs are calibrated
        # against. This is the most consequential thing the game could
        # do without being asked: it discards technologies you built,
        # which under fog are the only score there is, so defaulting it
        # on for a player would silently delete their work. Nothing
        # stops a player shedding a loss-maker by hand - `mothball` does
        # exactly that, and gets it back with `restore`.
        "auto_shed":     not manual,
        # Open every concern that plainly pays for itself. On for the
        # optimizer, whose long runs are calibrated against a household
        # that does run what it builds, and off for a player, for whom
        # deciding what to actually operate is the point.
        "auto_open":     not manual,
        "auto_court_heir": not manual,  # court a dead patron's successor
        # Buy a job from an outside shop when a few pairs of hands are the
        # only thing standing between you and something you need.
        "auto_commission": not manual,
        "auto_bribe":    not manual,   # pay your way out of a scandal
        # Rehire a specialist foreman an open concern has lost. Off by
        # default in manual play, and off unattended too: the optimizer's
        # auto_hire already replaces trades that concerns draw on.
        "auto_replace_foreman": False,
        # Keep `reserve` spare craftsmen and scholars above what open
        # concerns hold, hiring and housing them each year. Off always.
        "reserve_staff": False,
    }
