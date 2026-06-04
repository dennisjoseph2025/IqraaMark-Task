from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile
from authentication.models import User
from internships.models import Internship
from .models import Application


class ApplyInternshipTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/applications/apply/'
        self.company = User.objects.create_user(
            username='company1',
            email='company@example.com',
            password='StrongPass123!',
            role='company',
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='StrongPass123!',
            role='student',
        )
        self.other_student = User.objects.create_user(
            username='student2',
            email='student2@example.com',
            password='StrongPass123!',
            role='student',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Engineer Intern',
            description='Build cool stuff',
            location='Remote',
            duration='3 months',
        )
        student_login = self.client.post('/api/auth/login/', {
            'email': 'student@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.student_token = student_login.data['access']

        other_login = self.client.post('/api/auth/login/', {
            'email': 'student2@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.other_student_token = other_login.data['access']

        company_login = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.company_token = company_login.data['access']

    def test_apply_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['internship_title'], 'Software Engineer Intern')
        self.assertEqual(response.data['student_email'], 'student@example.com')
        self.assertEqual(Application.objects.count(), 1)

    def test_apply_duplicate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        self.client.post(self.url, {'internship': self.internship.id}, format='json')
        response = self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_apply_company_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_apply_unauthenticated(self):
        response = self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_apply_nonexistent_internship(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.post(self.url, {'internship': 999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_multiple_students_apply(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_student_token}')
        response = self.client.post(self.url, {'internship': self.internship.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Application.objects.count(), 2)


class ListApplicationsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/applications/'
        self.company = User.objects.create_user(
            username='company1',
            email='company@example.com',
            password='StrongPass123!',
            role='company',
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='StrongPass123!',
            role='student',
        )
        self.other_company = User.objects.create_user(
            username='company2',
            email='company2@example.com',
            password='StrongPass123!',
            role='company',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Engineer Intern',
            description='Build cool stuff',
            location='Remote',
            duration='3 months',
        )
        self.application = Application.objects.create(
            student=self.student,
            internship=self.internship,
        )

        student_login = self.client.post('/api/auth/login/', {
            'email': 'student@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.student_token = student_login.data['access']

        company_login = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.company_token = company_login.data['access']

        other_company_login = self.client.post('/api/auth/login/', {
            'email': 'company2@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.other_company_token = other_company_login.data['access']

    def test_list_applications_student(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['student_email'], 'student@example.com')

    def test_list_applications_student_sees_own_only(self):
        other_internship = Internship.objects.create(
            company=self.company,
            title='Data Scientist',
            description='ML',
            location='Remote',
            duration='3 months',
        )
        Application.objects.create(
            student=self.student,
            internship=other_internship,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.get(self.url)
        self.assertEqual(len(response.data), 2)

    def test_list_applications_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_applications_company_sees_own_only(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_company_token}')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_applications_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UpdateApplicationStatusTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.company = User.objects.create_user(
            username='company1',
            email='company@example.com',
            password='StrongPass123!',
            role='company',
        )
        self.other_company = User.objects.create_user(
            username='company2',
            email='company2@example.com',
            password='StrongPass123!',
            role='company',
        )
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='StrongPass123!',
            role='student',
        )
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Engineer Intern',
            description='Build cool stuff',
            location='Remote',
            duration='3 months',
        )
        self.application = Application.objects.create(
            student=self.student,
            internship=self.internship,
        )
        self.url = f'/api/applications/{self.application.id}/status/'

        company_login = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.company_token = company_login.data['access']

        other_login = self.client.post('/api/auth/login/', {
            'email': 'company2@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.other_company_token = other_login.data['access']

        student_login = self.client.post('/api/auth/login/', {
            'email': 'student@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.student_token = student_login.data['access']

    def test_update_status_accepted(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.patch(self.url, {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')

    def test_update_status_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.patch(self.url, {'status': 'rejected'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')

    def test_update_status_student_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.patch(self.url, {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_status_non_owner_company_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_company_token}')
        response = self.client.patch(self.url, {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_status_invalid_value(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.patch(self.url, {'status': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_update_status_unauthenticated(self):
        response = self.client.patch(self.url, {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_status_nonexistent_application(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.company_token}')
        response = self.client.patch('/api/applications/999/status/', {'status': 'accepted'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
