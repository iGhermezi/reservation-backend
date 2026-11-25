from datetime import date, time

from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from businesses.models import Business, Membership
from catalog.models import Provider, Service, WorkingHour


class FreeSlotsApiTests(APITestCase):
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
        self.flexible = Service.objects.create(
            business=self.business,
            name="ویزیت متغیر",
            price=100000,
            duration_type="flexible",
            min_minutes=30,
            max_minutes=120,
            step_minutes=30,
        )
        self.flexible.providers.add(self.provider)

    def test_free_slots_api_respects_duration_minutes(self):
        url = (
            f"/api/v1/free-slots/?provider={self.provider.id}"
            f"&service={self.flexible.id}&date=2026-11-28&duration_minutes=60"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["slots"],
            ["09:00", "09:30", "10:00", "10:30", "11:00"],
        )