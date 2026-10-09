"""What it costs in labourer-hours to lift a tonne one metre with the device a mine has: muscle through
a hand device, or an engine that needs attendants and fuel. Standalone: numbers in, hours out."""


def powered_hours_per_tonne_metre(engine, joules_per_tonne_metre, fuel_hours_per_kilogram):
    """Attendants' hours while the engine does the work, plus the labour of the fuel it burns.
    `engine` is (lift power in watts, attendants, fuel kilograms per tonne-metre)."""
    power_watts, attendants, fuel_kilograms = engine
    seconds_per_hour = 3600.0
    return (attendants * joules_per_tonne_metre / (power_watts * seconds_per_hour)
            + fuel_kilograms * fuel_hours_per_kilogram)


def cheapest_hours_per_tonne_metre(hand_hours, engines, joules_per_tonne_metre, fuel_hours_per_kilogram):
    """The lowest labour cost among the hand device and the engines a mine runs."""
    return min([hand_hours] + [powered_hours_per_tonne_metre(engine, joules_per_tonne_metre,
                                                             fuel_hours_per_kilogram)
                               for engine in engines or ()])
