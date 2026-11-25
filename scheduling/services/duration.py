def resolve_duration(service, duration_minutes):
    if service.duration_type == service.DurationType.FIXED:
        if duration_minutes is not None and duration_minutes != service.duration_minutes:
            raise ValueError("مدت خدمت ثابت است")
        return service.duration_minutes
    duration = duration_minutes or service.min_minutes
    if duration < service.min_minutes or duration > service.max_minutes:
        raise ValueError("مدت باید بین حداقل و حداکثر خدمت باشد")
    step = service.step_minutes or 15
    if (duration - service.min_minutes) % step != 0:
        raise ValueError("مدت باید مضرب گام خدمت باشد")
    return duration