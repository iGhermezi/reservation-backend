from datetime import datetime, time, timedelta

from django.utils import timezone

from .overlap import overlaps, subtract_interval
from .duration import resolve_duration

def get_free_slots(provider, service, date, duration_minutes=None):
    """ساعت‌های آزاد یک ارائه‌دهنده برای یک خدمت در یک روز."""
    duration = resolve_duration(service, duration_minutes)
    step = service.step_minutes or 15
    now = timezone.now()
    skip_past = date == timezone.localtime(now).date()
    slots = []

    if service.capacity == 1:
        for start, end in _free_intervals(provider, date, now):
            current = start
            while current + timedelta(minutes=duration) <= end:
                if not skip_past or current >= now:
                    slots.append(current.time())
                current += timedelta(minutes=step)
        return slots

    base_intervals = _base_intervals(provider, date)
    active = _active_appointments(provider, date, now)
    for start, end in base_intervals:
        current = start
        while current + timedelta(minutes=duration) <= end:
            if not skip_past or current >= now:
                candidate_end = current + timedelta(minutes=duration)
                count = 0
                for appt in active:
                    appt_start = timezone.localtime(appt.start_at)
                    appt_end = timezone.localtime(appt.end_at)
                    if overlaps(current, candidate_end, appt_start, appt_end):
                        count += 1
                if count < service.capacity:
                    slots.append(current.time())
            current += timedelta(minutes=step)
    return slots


def _base_intervals(provider, date):
    """ساعت کاری منهای مرخصی، بدون کم کردن نوبت‌ها."""
    our_weekday = (date.weekday() + 2) % 7
    intervals = []
    for wh in provider.working_hours.filter(weekday=our_weekday):
        intervals.append((
            timezone.make_aware(datetime.combine(date, wh.start_time)),
            timezone.make_aware(datetime.combine(date, wh.end_time)),
        ))
    for to in provider.time_offs.filter(date=date):
        if to.start_time is None and to.end_time is None:
            return []
        if to.start_time is None or to.end_time is None:
            continue
        off_start = timezone.make_aware(datetime.combine(date, to.start_time))
        off_end = timezone.make_aware(datetime.combine(date, to.end_time))
        intervals = [
            piece
            for start, end in intervals
            for piece in subtract_interval(start, end, off_start, off_end)
        ]
    return intervals


def _active_appointments(provider, date, now):
    """نوبت‌های فعال امروز، بدون هولدهای منقضی."""
    active_statuses = ["held", "pending_review", "awaiting_reupload", "confirmed"]
    day_start = timezone.make_aware(datetime.combine(date, time.min))
    day_end = timezone.make_aware(
        datetime.combine(date + timedelta(days=1), time.min)
    )
    return list(provider.appointments.filter(
        start_at__gte=day_start,
        start_at__lt=day_end,
        status__in=active_statuses,
    ).exclude(status="held", occupies_until__lt=now))


def _free_intervals(provider, date, now):
    """بازه‌های خالی = ساعت کاری منهای مرخصی منهای نوبت‌های فعال."""
    intervals = _base_intervals(provider, date)
    for appt in _active_appointments(provider, date, now):
        intervals = [
            piece
            for start, end in intervals
            for piece in subtract_interval(
                start,
                end,
                timezone.localtime(appt.start_at),
                timezone.localtime(appt.end_at),
            )
        ]
    return intervals
