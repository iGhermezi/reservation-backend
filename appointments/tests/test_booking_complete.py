from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from appointments.services.cancel_booking import cancel_appointment
from appointments.services.create_booking import (
    BookingValidationError,
    create_booking,
)
from appointments.services.custom_fields import (
    calculate_final_price,
    validate_custom_values,
)
from appointments.services.reschedule_booking import reschedule_appointment
from businesses.models import Business
from catalog.models import CustomFieldDefinition, Provider, Service, ServiceAddon, WorkingHour

User = get_user_model()


class BookingCompleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "+989120000001", password="SecurePassword!123"
        )
        self.other_user = User.objects.create_user(
            "+989120000002", password="SecurePassword!123"
        )
        self.business = Business.objects.create(
            name="کلینیک تست", slug="test-clinic", city="کرمان"
        )
        self.provider = Provider.objects.create(
            business=self.business, display_name="دکتر احمدی"
        )
        self.service = Service.objects.create(
            business=self.business,
            name="ویزیت",
            price=100000,
            duration_minutes=30,
            step_minutes=30,
            deposit_amount=50000,
            capacity=1,
        )
        self.service.providers.add(self.provider)
        WorkingHour.objects.create(
            provider=self.provider, weekday=0,  # شنبه
            start_time="09:00", end_time="12:00",
        )
        self.field = CustomFieldDefinition.objects.create(
            service=self.service, key="companions", label="تعداد همراه",
            field_type="number", is_required=True, unit_price=20000,
        )
        self.addon = ServiceAddon.objects.create(
            service=self.service, name="نسخه اضافه", price=30000
        )
        self.saturday = datetime(2026, 11, 28, 9, 0, tzinfo=timezone.get_current_timezone())

    def make_booking(self, **kwargs):
        kwargs.setdefault("custom_values", {"companions": 1})
        return create_booking(
            customer=self.user,
            provider_id=self.provider.id,
            service=self.service,
            start_at=self.saturday,
            **kwargs,
        )

    # --- فیلد سفارشی و قیمت ---

    def test_missing_required_field_fails(self):
        with self.assertRaises(ValueError):
            validate_custom_values(self.service, {})

    def test_unknown_field_fails(self):
        with self.assertRaises(ValueError):
            validate_custom_values(self.service, {"companions": 1, "nope": 1})

    def test_wrong_type_fails(self):
        with self.assertRaises(ValueError):
            validate_custom_values(self.service, {"companions": "two"})

    def test_negative_number_fails(self):
        with self.assertRaises(ValueError):
            validate_custom_values(self.service, {"companions": -1})

    def test_float_number_fails(self):
        with self.assertRaises(ValueError):
            validate_custom_values(self.service, {"companions": 1.5})

    def test_price_includes_custom_field_and_addon(self):
        price = calculate_final_price(
            self.service, {"companions": 2}, addon_ids=[self.addon.id]
        )
        self.assertEqual(price, 100000 + 40000 + 30000)

    def test_booking_stores_custom_values_and_deposit_unchanged(self):
        appt = self.make_booking(custom_values={"companions": 2}, addon_ids=[self.addon.id])
        self.assertEqual(appt.price_final, 100000 + 40000 + 30000)
        self.assertEqual(appt.deposit_amount, 50000)
        self.assertEqual(appt.custom_values, {"companions": 2})

    # --- لغو ---

    def test_cancel_more_than_24h_refunds_85_percent(self):
        appt = self.make_booking()
        result = cancel_appointment(appt, by_user=self.user)
        self.assertEqual(result["refund_rate"], Decimal("0.85"))
        self.assertEqual(result["refund_amount"], 50000 * Decimal("0.85"))
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.CANCELLED)

    def test_cancel_twice_fails(self):
        appt = self.make_booking()
        cancel_appointment(appt, by_user=self.user)
        with self.assertRaises(Exception):
            cancel_appointment(appt, by_user=self.user)

    def test_cancel_by_other_user_fails(self):
        appt = self.make_booking()
        with self.assertRaises(Exception):
            cancel_appointment(appt, by_user=self.other_user)

    def test_cancel_expired_hold_fails_and_marks_expired(self):
        appt = self.make_booking()
        appt.occupies_until = timezone.now() - timedelta(minutes=1)
        appt.save(update_fields=["occupies_until"])
        with self.assertRaises(Exception):
            cancel_appointment(appt, by_user=self.user)
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.EXPIRED)

    # --- تغییر زمان ---

    def test_reschedule_once_succeeds(self):
        appt = self.make_booking()
        new_start = self.saturday + timedelta(hours=1)
        updated = reschedule_appointment(appt, by_user=self.user, new_start_at=new_start)
        self.assertEqual(updated.start_at, new_start)
        self.assertEqual(updated.reschedule_count, 1)

    def test_reschedule_twice_fails(self):
        appt = self.make_booking()
        reschedule_appointment(
            appt, by_user=self.user,
            new_start_at=self.saturday + timedelta(hours=1),
        )
        with self.assertRaises(Exception):
            reschedule_appointment(
                appt, by_user=self.user,
                new_start_at=self.saturday + timedelta(hours=2),
            )

    def test_reschedule_too_close_to_new_start_fails(self):
        appt = self.make_booking()
        soon = timezone.now() + timedelta(hours=3)
        with self.assertRaises(Exception):
            reschedule_appointment(appt, by_user=self.user, new_start_at=soon)

    # --- لاگ و تایم‌لاین ---

    def test_created_log_exists(self):
        appt = self.make_booking()
        self.assertTrue(appt.logs.filter(action="created").exists())

    def test_timeline_api_returns_logs(self):
        appt = self.make_booking()
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(f"/api/v1/bookings/{appt.public_id}/timeline/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["action"], "created")

    def test_timeline_after_cancel_has_two_logs(self):
        appt = self.make_booking()
        cancel_appointment(appt, by_user=self.user)
        client = APIClient()
        client.force_authenticate(user=self.user)
        response = client.get(f"/api/v1/bookings/{appt.public_id}/timeline/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[1]["action"], "cancelled")

    def test_timeline_for_other_user_is_404(self):
        appt = self.make_booking()
        client = APIClient()
        client.force_authenticate(user=self.other_user)
        response = client.get(f"/api/v1/bookings/{appt.public_id}/timeline/")
        self.assertEqual(response.status_code, 404)