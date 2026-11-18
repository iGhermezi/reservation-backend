from django.test import TestCase

from businesses.models import Business


class BusinessSlugTests(TestCase):
    def setUp(self):
        self.business = Business.objects.create(
            name="Test Business",
            slug="test-business",
            city="Tehran",
        )

    def test_slug_cannot_be_changed(self):
        self.business.slug = "new-slug"
        with self.assertRaisesMessage(ValueError, "slug قابل تغییر نیست"):
            self.business.save()

    def test_business_can_be_saved_without_changing_slug(self):
        self.business.name = "Updated Business"
        self.business.save()

        self.business.refresh_from_db()
        self.assertEqual(self.business.name, "Updated Business")
        self.assertEqual(self.business.slug, "test-business")
