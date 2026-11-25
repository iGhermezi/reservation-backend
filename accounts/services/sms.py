import logging

logger = logging.getLogger(__name__)


class SmsProvider:
    def send(self, phone_number, code):
        raise NotImplementedError

class LogProvider(SmsProvider):
    """توی دولوپمنت کد رو توی کنسول چاپ می‌کنه؛ پیامک واقعی فاز ۲ است."""
    def send(self, phone_number, code):
        print(f"OTP for {phone_number}: {code}")