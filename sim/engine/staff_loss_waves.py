"""Staff loss from a dated hazard arrives as independent yearly waves; this is the exposure over the years left."""


def wave_exposure(wave_chance, loss_per_wave, year_start, year_end, current_year):
    """Waves still to be checked, the chance of at least one, and the expected cumulative loss."""
    waves = max(1, year_end - max(year_start, current_year) + 1)
    return {"remaining_annual_wave_checks": waves,
            "chance_of_at_least_one_staff_loss_wave": round(1.0 - (1.0 - wave_chance) ** waves, 4),
            "expected_cumulative_staff_loss": round(1.0 - (1.0 - wave_chance * loss_per_wave) ** waves, 4)}
