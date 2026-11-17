from datetime import date, time, datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from appointments.services.create_booking import SlotTakenError, create_booking
from businesses.models import Business, Membership
from catalog.models import Service, Provider, WorkingHour


class CreateBookingTests(TestCase):
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
        self.start = timezone.make_aware(datetime(2026, 11, 14, 10, 0))

    def test_booking_creates_held_appointment(self):
        appt = create_booking(
            customer=self.user,
            provider_id=self.provider.id,
            service=self.service,
            start_at=self.start,
        )
        self.assertEqual(appt.status, Appointment.Status.HELD)
        self.assertEqual(appt.start_at, self.start)
        self.assertEqual(appt.end_at, self.start + timedelta(minutes=30))
        self.assertEqual(appt.price_final, 100000)
        self.assertIsNotNone(appt.occupies_until)

    def test_second_booking_same_slot_fails(self):
        create_booking(
            customer=self.user,
            provider_id=self.provider.id,
            service=self.service,
            start_at=self.start,
        )
        with self.assertRaises(SlotTakenError):
            create_booking(
                customer=self.user,
                provider_id=self.provider.id,
                service=self.service,
                start_at=self.start,
            )

    def test_expired_hold_frees_slot(self):
        appt = create_booking(
            customer=self.user,
            provider_id=self.provider.id,
            service=self.service,
            start_at=self.start,
        )
        appt.occupies_until = timezone.now() - timedelta(minutes=1)
        appt.save()
        new_appt = create_booking(
            customer=self.user,
            provider_id=self.provider.id,
            service=self.service,
            start_at=self.start,
        )
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.EXPIRED)
        self.assertEqual(new_appt.status, Appointment.Status.HELD)
