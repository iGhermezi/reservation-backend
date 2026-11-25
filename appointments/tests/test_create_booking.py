from datetime import date, time, datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from appointments.services.create_booking import BookingValidationError, SlotTakenError, create_booking
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
        self.start = timezone.make_aware(datetime(2026, 11, 28, 10, 0))

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


    def test_booking_provider_from_other_business_fails(self):
        other_business = Business.objects.create(
            name="کلینیک دوم", slug="test-clinic-2"
        )
        other_provider = Provider.objects.create(
            business=other_business, display_name="دکتر دوم"
        )
        with self.assertRaises(BookingValidationError):
            create_booking(
                customer=self.user,
                provider_id=other_provider.id,
                service=self.service,
                start_at=timezone.make_aware(datetime(2026, 11, 28, 10, 0)),
            )

    def test_booking_inactive_service_fails(self):
        self.service.is_active = False
        self.service.save()
        with self.assertRaises(BookingValidationError):
            create_booking(
                customer=self.user,
                provider_id=self.provider.id,
                service=self.service,
                start_at=timezone.make_aware(datetime(2026, 11, 28, 10, 0)),
            )

    def test_booking_past_date_fails(self):
        with self.assertRaises(BookingValidationError):
            create_booking(
                customer=self.user,
                provider_id=self.provider.id,
                service=self.service,
                start_at=timezone.make_aware(datetime(2026, 11, 14, 10, 0)),
            )

    def test_flexible_booking_invalid_duration_fails(self):
        flexible = Service.objects.create(
            business=self.business,
            name="ویزیت متغیر",
            price=100000,
            duration_type="flexible",
            min_minutes=30,
            max_minutes=120,
            step_minutes=15,
        )
        flexible.providers.add(self.provider)
        with self.assertRaises(BookingValidationError):
            create_booking(
                customer=self.user,
                provider_id=self.provider.id,
                service=flexible,
                start_at=self.start,
                duration_minutes=40,
            )

    def test_capacity_2_third_booking_fails(self):
        group = Service.objects.create(
            business=self.business,
            name="کلاس گروهی",
            price=100000,
            duration_minutes=30,
            step_minutes=30,
            capacity=2,
        )
        group.providers.add(self.provider)
        create_booking(
            customer=self.user, provider_id=self.provider.id,
            service=group, start_at=self.start,
        )
        create_booking(
            customer=self.user, provider_id=self.provider.id,
            service=group, start_at=self.start,
        )
        with self.assertRaises(SlotTakenError):
            create_booking(
                customer=self.user, provider_id=self.provider.id,
                service=group, start_at=self.start,
            )