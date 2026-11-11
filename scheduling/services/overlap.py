def overlaps(a_start, a_end, b_start, b_end):
    """دو بازه با هم تداخل دارن یا نه؟"""
    return a_start < b_end and a_end > b_start


def subtract_interval(free_start, free_end, busy_start, busy_end):
    """یه بازه شلوغ رو از یه بازه خالی کم کن؛ لیست بازه‌های باقی‌مونده رو برگردون."""
    if not overlaps(free_start, free_end, busy_start, busy_end):
        return [(free_start, free_end)]
    result = []
    if free_start < busy_start:
        result.append((free_start, busy_start))
    if busy_end < free_end:
        result.append((busy_end, free_end))
    return result
