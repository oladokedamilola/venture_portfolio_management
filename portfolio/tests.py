from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Startup, Project, Task, FundingRound
from django.urls import reverse

User = get_user_model()

class PortfolioModelTests(TestCase):
    def setUp(self):
        self.founder = User.objects.create_user(username="founder1", password="testpass", role="FOUNDER")
        self.team_member = User.objects.create_user(username="teammember1", password="testpass", role="TEAM")

        self.startup = Startup.objects.create(
            name="TechNova",
            description="AI assistant for startups",
            stage="MVP"
        )
        self.project = Project.objects.create(
            startup=self.startup,
            title="Build MVP",
            description="Core MVP development",
        )
        self.task = Task.objects.create(
            project=self.project,
            title="Design UI Mockups",
            assigned_to=self.team_member,
        )
        self.funding = FundingRound.objects.create(
            startup=self.startup,
            round_type="SEED",
            amount=100000,
            date="2024-02-15"
        )

    def test_startup_str(self):
        self.assertEqual(str(self.startup), "TechNova (MVP Development)")

    def test_project_links_to_startup(self):
        self.assertEqual(self.project.startup, self.startup)

    def test_task_assignment(self):
        self.assertEqual(self.task.assigned_to.username, "teammember1")

    def test_funding_round(self):
        self.assertEqual(self.funding.amount, 100000)
        self.assertEqual(str(self.funding), "TechNova - Seed - $100000")

from portfolio.models import Task, Project

class TaskVisibilityTests(TestCase):
    def setUp(self):
        self.team_member = User.objects.create_user(username="team1", password="testpass", role="TEAM")
        self.other_member = User.objects.create_user(username="team2", password="testpass", role="TEAM")
        self.startup = Startup.objects.create(name="EduVerse", stage="MVP")
        self.project = Project.objects.create(startup=self.startup, title="VR Classroom")

        self.task1 = Task.objects.create(project=self.project, title="Build VR Environment", assigned_to=self.team_member)
        self.task2 = Task.objects.create(project=self.project, title="Test VR Lessons", assigned_to=self.other_member)

    def test_team_member_sees_only_own_tasks(self):
        self.client.login(username="team1", password="testpass")
        response = self.client.get(reverse("startup_list"))
        self.assertContains(response, "Build VR Environment")
        self.assertNotContains(response, "Test VR Lessons")
