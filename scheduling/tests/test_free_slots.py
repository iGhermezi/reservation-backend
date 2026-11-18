from datetime import date, time, datetime, timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from accounts.models import User
from businesses.models import Business, Membership
from catalog.models import Service, Provider, TimeOff, WorkingHour
from appointments.models import Appointment
from scheduling.services.free_slots import get_free_slots


class FreeSlotsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone_number="+989121234567",
            first_name="متین",
            last_name="زاهدی",
            password="test1234",
        )
        self.business = Business.objects.create(
            name="کلینیک تست", slug="test-clinic"
        )
        Membership.objects.create(
            user=self.user, business=self.business, role="owner"
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
        )
        self.service.providers.add(self.provider)
        WorkingHour.objects.create(
            provider=self.provider,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        self.day = date(2026, 11, 14)  # شنبه

    def test_free_slots_without_appointments(self):
        slots = get_free_slots(self.provider, self.service, self.day)
        self.assertEqual(
            [s.strftime("%H:%M") for s in slots],
            ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"],
        )

    def test_free_slots_minus_confirmed_appointment(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.user,
            provider=self.provider,
            service=self.service,
            start_at=timezone.make_aware(datetime(2026, 11, 14, 10, 0)),
            end_at=timezone.make_aware(datetime(2026, 11, 14, 10, 30)),
            duration_minutes=30,
            price_final=100000,
            deposit_amount=0,
            status="confirmed",
        )
        slots = get_free_slots(self.provider, self.service, self.day)
        self.assertEqual(
            [s.strftime("%H:%M") for s in slots],
            ["09:00", "09:30", "10:30", "11:00", "11:30"],
        )

    def test_past_slots_today_are_skipped(self):
        fixed_now = timezone.make_aware(
            datetime.combine(timezone.localdate(), time(9, 45))
        )
        weekday = (fixed_now.date().weekday() + 2) % 7
        WorkingHour.objects.create(
            provider=self.provider,
            weekday=weekday,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )

        with patch("scheduling.services.free_slots.timezone.now", return_value=fixed_now):
            slots = get_free_slots(self.provider, self.service, fixed_now.date())

        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots],
            ["10:00", "10:30", "11:00", "11:30"],
        )

    def test_partial_time_off_is_ignored(self):
        TimeOff.objects.create(
            provider=self.provider,
            date=self.day,
            start_time=time(10, 0),
        )

        slots = get_free_slots(self.provider, self.service, self.day)

        self.assertEqual(
            [slot.strftime("%H:%M") for slot in slots],
            ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30"],
        )

    def test_expired_hold_does_not_block_slot(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.user,
            provider=self.provider,
            service=self.service,
            start_at=timezone.make_aware(datetime(2026, 11, 14, 10, 0)),
            end_at=timezone.make_aware(datetime(2026, 11, 14, 10, 30)),
            duration_minutes=30,
            price_final=100000,
            deposit_amount=0,
            status=Appointment.Status.HELD,
            occupies_until=timezone.now() - timedelta(minutes=1),
        )

        slots = get_free_slots(self.provider, self.service, self.day)

        self.assertIn("10:00", [slot.strftime("%H:%M") for slot in slots])

    def test_cancelled_appointment_frees_slot(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.user,
            provider=self.provider,
            service=self.service,
            start_at=timezone.make_aware(datetime(2026, 11, 14, 10, 0)),
            end_at=timezone.make_aware(datetime(2026, 11, 14, 10, 30)),
            duration_minutes=30,
            price_final=100000,
            deposit_amount=0,
            status="cancelled",
        )
        slots = get_free_slots(self.provider, self.service, self.day)
        self.assertIn("10:00", [s.strftime("%H:%M") for s in slots])
