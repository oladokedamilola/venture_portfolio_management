from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from portfolio.models import Startup

User = get_user_model()

class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="manager", password="testpass", role="MANAGER")
        self.investor = User.objects.create_user(username="investor", password="testpass", role="INVESTOR")
        self.startup = Startup.objects.create(name="GreenSpark", stage="IDEA")

    def test_manager_can_create_startup(self):
        self.client.login(username="manager", password="testpass")
        response = self.client.post(reverse("startup_create"), {
            "name": "NewStartup",
            "description": "Test startup",
            "stage": "MVP"
        })
        self.assertEqual(response.status_code, 302)  # redirect after success
        self.assertTrue(Startup.objects.filter(name="NewStartup").exists())

    def test_investor_cannot_create_startup(self):
        self.client.login(username="investor", password="testpass")
        response = self.client.get(reverse("startup_create"))
        self.assertNotEqual(response.status_code, 200)  # blocked
