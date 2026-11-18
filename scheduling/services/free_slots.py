from datetime import datetime, time, timedelta

from django.utils import timezone

from .overlap import subtract_interval


def get_free_slots(provider, service, date):
    """ساعت‌های آزاد یک ارائه‌دهنده برای یک خدمت در یک روز."""
    duration = service.duration_minutes or service.min_minutes
    step = service.step_minutes or 15
    now = timezone.now()
    skip_past = date == timezone.localtime(now).date()
    slots = []
    for start, end in _free_intervals(provider, date):
        current = start
        while current + timedelta(minutes=duration) <= end:
            if not skip_past or current >= now:
                slots.append(current.time())
            current += timedelta(minutes=step)
    return slots


def _free_intervals(provider, date):
    """بازه‌های خالی = ساعت کاری منهای مرخصی منهای نوبت‌های فعال."""
    now = timezone.now()
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
    active_statuses = ["held", "pending_review", "awaiting_reupload", "confirmed"]
    day_start = timezone.make_aware(datetime.combine(date, time.min))
    day_end = timezone.make_aware(
        datetime.combine(date + timedelta(days=1), time.min)
    )
    for appt in provider.appointments.filter(
        start_at__gte=day_start,
        start_at__lt=day_end,
        status__in=active_statuses,
    ).exclude(status="held", occupies_until__lt=now):
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
