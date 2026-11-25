from decimal import Decimal, InvalidOperation

from catalog.models import ServiceAddon


def validate_custom_values(service, values):
    """مقادیر فیلدهای سفارشی رو چک کن؛ اگه چیزی غلط بود ValueError بده."""
    if values is None:
        values = {}
    if not isinstance(values, dict):
        raise ValueError("مقادیر فیلدهای سفارشی باید دیکشنری باشد")

    definitions = service.custom_fields.all()
    defined_keys = {definition.key for definition in definitions}

    for key in values:
        if key not in defined_keys:
            raise ValueError(f"فیلد ناشناخته: {key}")

    for definition in definitions:
        if definition.key not in values:
            if definition.is_required:
                raise ValueError(f"فیلد {definition.label} الزامی است")
            continue

        value = values[definition.key]
        field_type = definition.field_type

        if field_type == "text":
            if not isinstance(value, str):
                raise ValueError(f"فیلد {definition.label} باید متن باشد")
        elif field_type == "number":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"فیلد {definition.label} باید عدد صحیح باشد")
            if value < 0:
                raise ValueError(f"فیلد {definition.label} نمی‌تواند منفی باشد")
        elif field_type == "choice":
            if value not in definition.choices:
                raise ValueError(f"مقدار فیلد {definition.label} معتبر نیست")
        elif field_type == "boolean":
            if not isinstance(value, bool):
                raise ValueError(f"فیلد {definition.label} باید درست یا غلط باشد")

    return values


def calculate_final_price(service, values, addon_ids=None):
    """قیمت نهایی: قیمت سرویس + ادان‌ها + هزینه فیلدهای سفارشی."""
    if values is None:
        values = {}
    total = service.price

    if addon_ids:
        addon_ids = set(addon_ids)
        addons = ServiceAddon.objects.filter(
            service=service, id__in=addon_ids, is_active=True
        )
        if addons.count() != len(addon_ids):
            raise ValueError("ادان نامعتبر است")
        for addon in addons:
            total += addon.price

    definitions = service.custom_fields.all()
    for definition in definitions:
        if definition.unit_price is None:
            continue
        if definition.key not in values:
            continue

        value = values[definition.key]
        if definition.field_type == "number":
            try:
                numeric_value = Decimal(str(value))
            except (TypeError, InvalidOperation) as exc:
                raise ValueError(
                    f"مقدار فیلد {definition.label} معتبر نیست"
                ) from exc
            total += definition.unit_price * numeric_value
        elif definition.field_type in ("boolean", "choice"):
            if value:
                total += definition.unit_price

    if total <= 0:
        raise ValueError("قیمت نهایی باید بیشتر از صفر باشد")
    return total