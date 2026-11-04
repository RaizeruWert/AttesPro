from django.test import TestCase
from django.contrib.auth.models import User
from .models import Assignment, AttestationApplication

class MultipleAssignmentsTest(TestCase):
    def test_one_user_can_have_management_and_teaching_roles(self):
        user = User.objects.create_user(username="teacher", password="StrongPass123!")
        director = Assignment.objects.create(user=user, kind="management", position="Заместитель директора")
        teacher = Assignment.objects.create(user=user, kind="pedagogical", position="Учитель", subject="Молдавский язык")
        self.assertEqual(user.assignments.count(), 2)
        app1 = AttestationApplication.objects.create(user=user, assignment=director)
        app2 = AttestationApplication.objects.create(user=user, assignment=teacher)
        self.assertNotEqual(app1.assignment_id, app2.assignment_id)
