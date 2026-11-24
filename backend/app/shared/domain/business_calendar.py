"""Colombian business-day calendar (no Saturdays, Sundays or public holidays)."""

from collections.abc import Iterable
from datetime import date, timedelta
from functools import lru_cache

import holidays


@lru_cache
def _colombian_holidays(year: int) -> frozenset[date]:
    return frozenset(holidays.country_holidays("CO", years=year).keys())


class BusinessCalendar:
    def __init__(self, extra_holidays: Iterable[date] = ()):
        self._extra = frozenset(extra_holidays)

    def is_holiday(self, day: date) -> bool:
        return day in _colombian_holidays(day.year) or day in self._extra

    def is_business_day(self, day: date) -> bool:
        return day.weekday() < 5 and not self.is_holiday(day)

    def next_business_day(self, day: date) -> date:
        day += timedelta(days=1)
        while not self.is_business_day(day):
            day += timedelta(days=1)
        return day

    def add_business_days(self, received: date, days: int) -> date:
        """Due date: counting starts on the business day after reception."""
        day = received
        for _ in range(days):
            day = self.next_business_day(day)
        return day

    def holidays_in_term(self, received: date, days: int) -> list[date]:
        """Public holidays that fall inside a business-day term."""
        due = self.add_business_days(received, days)
        span = (received + timedelta(days=i) for i in range(1, (due - received).days))
        return [d for d in span if self.is_holiday(d)]

    def is_holiday_between(self, received: date, days: int) -> bool:
        return bool(self.holidays_in_term(received, days))

    def business_days_between(self, start: date, end: date) -> int:
        """Business days strictly between two dates (both ends excluded)."""
        count, day = 0, start + timedelta(days=1)
        while day < end:
            count += self.is_business_day(day)
            day += timedelta(days=1)
        return count
