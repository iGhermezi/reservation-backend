from datetime import time

from rest_framework.test import APITestCase

from accounts.models import User
from businesses.models import Business, Membership
from catalog.models import Provider, Service, WorkingHour


class BookingApiTests(APITestCase):
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
        WorkingHour.objects.create(
            provider=self.provider,
            weekday=0,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        self.group = Service.objects.create(
            business=self.business,
            name="کلاس گروهی",
            price=100000,
            duration_minutes=30,
            step_minutes=30,
            capacity=2,
        )
        self.group.providers.add(self.provider)
        self.client.force_authenticate(user=self.user)

    def test_group_booking_outside_working_hours_fails(self):
        response = self.client.post(
            "/api/v1/bookings/",
            {
                "provider": self.provider.id,
                "service": self.group.id,
                "start_at": "2026-11-28T03:00:00+03:30",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 409)