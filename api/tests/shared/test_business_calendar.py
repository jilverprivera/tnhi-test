from datetime import date

from app.shared.domain.business_calendar import BusinessCalendar

cal = BusinessCalendar()


def test_colombian_holidays_of_the_case_are_not_business_days():
    assert cal.is_holiday(date(2026, 11, 16))  # Independencia de Cartagena (moved to Monday)
    assert cal.is_holiday(date(2026, 12, 8))  # Inmaculada Concepción
    assert not cal.is_business_day(date(2026, 11, 14))  # Saturday


def test_term_counts_from_the_next_business_day():
    # Interview example: petition received 10-nov, 15 business days, 16-nov is a holiday
    assert cal.add_business_days(date(2026, 11, 10), 15) == date(2026, 12, 2)


def test_term_received_on_friday_skips_weekend_and_holiday():
    assert cal.add_business_days(date(2026, 11, 13), 5) == date(2026, 11, 23)


def test_term_crossing_december_8():
    assert cal.add_business_days(date(2026, 11, 17), 15) == date(2026, 12, 9)


def test_holidays_in_term_lists_them():
    assert cal.holidays_in_term(date(2026, 11, 10), 15) == [date(2026, 11, 16)]


def test_business_days_between_excludes_both_ends():
    assert cal.business_days_between(date(2026, 11, 17), date(2026, 11, 19)) == 1
    assert cal.business_days_between(date(2026, 11, 17), date(2026, 11, 30)) == 8


def test_extra_holidays_are_respected():
    custom = BusinessCalendar([date(2026, 11, 18)])
    assert not custom.is_business_day(date(2026, 11, 18))
