from appointments.models import AppointmentLog


def log_appointment(appointment, action, actor=None, note=""):
    return AppointmentLog.objects.create(
        appointment=appointment,
        action=action,
        actor=actor,
        note=note,
    )
