import re

from rest_framework.exceptions import ValidationError


_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)
_PHONE_PATTERN = re.compile(r"^\+98\d{10}$")
_SEPARATORS = re.compile(r"[\s\-\u2010-\u2015\u2212]+")


def normalize_phone(value):
    phone_number = _SEPARATORS.sub("", str(value).translate(_DIGIT_TRANSLATION))
    if phone_number.startswith("09"):
        phone_number = "+98" + phone_number[1:]
    elif phone_number.startswith("989"):
        phone_number = "+" + phone_number

    if not _PHONE_PATTERN.fullmatch(phone_number):
        raise ValidationError("Enter a valid Iranian phone number.")
    return phone_number
