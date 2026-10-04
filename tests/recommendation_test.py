from datetime import date

from app.core.enums import CyclePhase
from app.recommendation.service import calculate_cycle_length, calculate_cycle_phase

# Reference cycle: 28-day cycle, 5-day period, starting 2026-09-01.
# luteal_start_day = 28 - 14 + 1 = 15, ovulatory_start_day = 15 - 3 = 12
# day 1-5 menstrual, day 6-11 follicular, day 12-14 ovulatory, day 15-28 luteal
LAST_PERIOD_START = date(2026, 9, 1)
CYCLE_LENGTH_DAYS = 28
PERIOD_LENGTH_DAYS = 5


def test_calculate_cycle_phase_menstrual_on_day_one():
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 1)
    )
    assert phase == CyclePhase.menstrual


def test_calculate_cycle_phase_menstrual_on_last_period_day():
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 5)
    )
    assert phase == CyclePhase.menstrual


def test_calculate_cycle_phase_follicular():
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 8)
    )
    assert phase == CyclePhase.follicular


def test_calculate_cycle_phase_ovulatory():
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 13)
    )
    assert phase == CyclePhase.ovulatory


def test_calculate_cycle_phase_luteal():
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 20)
    )
    assert phase == CyclePhase.luteal


def test_calculate_cycle_phase_wraps_to_next_cycle():
    # Day 1 of the *second* cycle (28 days later) should still be menstrual.
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, CYCLE_LENGTH_DAYS, PERIOD_LENGTH_DAYS, date(2026, 9, 29)
    )
    assert phase == CyclePhase.menstrual


def test_calculate_cycle_phase_adapts_to_longer_cycle():
    # A 32-day cycle pushes luteal/ovulatory later: luteal_start = 32-14+1 = 19,
    # ovulatory_start = 19-3 = 16. Day 17 should now be ovulatory, not luteal.
    phase = calculate_cycle_phase(
        LAST_PERIOD_START, 32, PERIOD_LENGTH_DAYS, date(2026, 9, 17)
    )
    assert phase == CyclePhase.ovulatory


def test_calculate_cycle_length_with_two_entries():
    length = calculate_cycle_length([date(2026, 8, 1), date(2026, 8, 29)])
    assert length == 28


def test_calculate_cycle_length_with_fewer_than_two_entries_returns_none():
    assert calculate_cycle_length([]) is None
    assert calculate_cycle_length([date(2026, 8, 1)]) is None


def test_calculate_cycle_length_uses_most_recent_two_of_many():
    # Older gap is 30 days, most recent gap is 26 days - should use the recent one.
    starts = [date(2026, 7, 1), date(2026, 7, 31), date(2026, 8, 26)]
    assert calculate_cycle_length(starts) == 26
