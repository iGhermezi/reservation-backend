from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import OtpCode, User
from accounts.serializers.auth import RegisterSerializer, SetPasswordSerializer
from accounts.services.otp import OtpError, request_otp, verify_otp
from accounts.services.phone import normalize_phone


class NormalizePhoneTests(SimpleTestCase):
    def test_normalizes_local_and_non_latin_digits(self):
        self.assertEqual(normalize_phone("۰۹۱۲-۳۴۵ ۶۷۸۹"), "+989123456789")
        self.assertEqual(normalize_phone("989123456789"), "+989123456789")
        self.assertEqual(normalize_phone("+989123456789"), "+989123456789")

    def test_rejects_invalid_phone_number(self):
        with self.assertRaises(ValidationError):
            normalize_phone("0912345")


class AuthFlowTests(TestCase):
    def create_otp(self, phone_number, code="123456"):
        return OtpCode.objects.create(
            phone_number=phone_number,
            code_hash=make_password(code),
            expires_at=timezone.now() + timedelta(minutes=5),
        )

    def test_registration_creates_user_without_usable_password(self):
        serializer = RegisterSerializer(
            data={
                "phone_number": "۰۹۱۲-۳۴۵۶۷۸۹",
                "first_name": "Test",
                "last_name": "User",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertEqual(user.phone_number, "+989123456789")
        self.assertFalse(user.has_usable_password())

    def test_registration_rejects_password(self):
        serializer = RegisterSerializer(
            data={
                "phone_number": "+989123456789",
                "password": "SecurePassword!123",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_set_password_requires_confirmation_and_password_validation(self):
        user = User.objects.create_user("+989123456789", password=None)
        request = type("Request", (), {"user": user})()

        mismatch = SetPasswordSerializer(
            data={
                "password": "SecurePassword!123",
                "password_confirm": "different",
            },
            context={"request": request},
        )
        self.assertFalse(mismatch.is_valid())

        weak = SetPasswordSerializer(
            data={"password": "password", "password_confirm": "password"},
            context={"request": request},
        )
        self.assertFalse(weak.is_valid())

    def test_set_password_endpoint_sets_authenticated_user_password(self):
        user = User.objects.create_user("+989123456789", password=None)
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            "/api/v1/auth/set-password/",
            {
                "password": "SecurePassword!123",
                "password_confirm": "SecurePassword!123",
            },
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(check_password("SecurePassword!123", user.password))

    def test_verification_wipes_unclaimed_password_and_consumes_otp(self):
        phone_number = "+989123456789"
        user = User.objects.create_user(phone_number, password="OldPassword!123")
        otp = self.create_otp(phone_number)

        verified_user = verify_otp(phone_number, "123456")

        user.refresh_from_db()
        otp.refresh_from_db()
        self.assertEqual(verified_user.pk, user.pk)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(otp.is_used)
        with self.assertRaises(OtpError):
            verify_otp(phone_number, "123456")

    def test_wrong_otp_attempt_is_committed(self):
        phone_number = "+989123456789"
        otp = self.create_otp(phone_number)

        with self.assertRaises(OtpError):
            verify_otp(phone_number, "000000")

        otp.refresh_from_db()
        self.assertEqual(otp.attempts, 1)

    def test_otp_login_does_not_wipe_verified_password(self):
        phone_number = "+989123456789"
        user = User.objects.create_user(
            phone_number,
            password="ExistingPassword!123",
            account_state=User.AccountState.VERIFIED,
        )
        self.create_otp(phone_number)

        verify_otp(phone_number, "123456")

        user.refresh_from_db()
        self.assertTrue(check_password("ExistingPassword!123", user.password))

    def test_inactive_user_cannot_verify_otp(self):
        phone_number = "+989123456789"
        User.objects.create_user(phone_number, is_active=False)
        otp = self.create_otp(phone_number)

        with self.assertRaises(OtpError):
            verify_otp(phone_number, "123456")

        otp.refresh_from_db()
        self.assertFalse(otp.is_used)

    @override_settings(DEBUG=False)
    def test_sms_provider_is_required_outside_debug(self):
        with self.assertRaisesMessage(OtpError, "SMS provider not configured"):
            request_otp("+989123456789")
        self.assertFalse(OtpCode.objects.exists())

    @override_settings(DEBUG=False)
    def test_request_otp_returns_503_without_provider(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = client.post(
            "/api/v1/auth/request-otp/",
            {"phone_number": "+989123456789"},
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data["code"], "sms_unavailable")

    @override_settings(DEBUG=True)
    def test_failed_sms_delivery_removes_otp_row(self):
        class FailingProvider:
            def send(self, phone_number, code):
                raise RuntimeError("provider internals")

        with self.assertRaisesMessage(OtpError, "SMS delivery failed"):
            request_otp("+989123456789", provider=FailingProvider())
        self.assertFalse(OtpCode.objects.exists())

    def test_unverified_password_login_does_not_return_tokens(self):
        User.objects.create_user("+989123456789", password="SecurePassword!123")

        response = APIClient().post(
            "/api/v1/auth/login/",
            {"phone_number": "+989123456789", "password": "SecurePassword!123"},
        )

        self.assertEqual(response.status_code, 401)
        self.assertNotIn("access", response.data)
