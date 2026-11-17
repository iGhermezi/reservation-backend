from datetime import datetime, timedelta

from django.utils import timezone

from .overlap import subtract_interval


def get_free_slots(provider, service, date):
    """ساعت‌های آزاد یک ارائه‌دهنده برای یک خدمت در یک روز."""
    duration = service.duration_minutes or service.min_minutes
    step = service.step_minutes or 15
    slots = []
    for start, end in _free_intervals(provider, date):
        current = start
        while current + timedelta(minutes=duration) <= end:
            slots.append(current.time())
            current += timedelta(minutes=step)
    return slots


def _free_intervals(provider, date):
    """بازه‌های خالی = ساعت کاری منهای مرخصی منهای نوبت‌های فعال."""
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
        off_start = timezone.make_aware(datetime.combine(date, to.start_time))
        off_end = timezone.make_aware(datetime.combine(date, to.end_time))
        intervals = [
            piece
            for start, end in intervals
            for piece in subtract_interval(start, end, off_start, off_end)
        ]
    active_statuses = ["held", "pending_review", "awaiting_reupload", "confirmed"]
    for appt in provider.appointments.filter(
        start_at__date=date, status__in=active_statuses
    ):
        intervals = [
            piece
            for start, end in intervals
            for piece in subtract_interval(start, end, appt.start_at, appt.end_at)
        ]
    return intervals
