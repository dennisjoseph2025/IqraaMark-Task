from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from authentication.models import User
from .models import Internship


class InternshipListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/internships/'
        self.company = User.objects.create_user(
            username='company1',
            email='company@example.com',
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

    def test_list_internships_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Software Engineer Intern')
        self.assertEqual(response.data[0]['company_name'], 'company1')

    def test_list_internships_empty(self):
        self.internship.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class InternshipCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/internships/'
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
        self.valid_payload = {
            'title': 'Backend Developer Intern',
            'description': 'Work on APIs',
            'location': 'New York',
            'duration': '6 months',
        }
        login_res = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.token = login_res.data['access']

    def test_create_internship_company(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Backend Developer Intern')
        self.assertEqual(response.data['company_name'], 'company1')
        self.assertEqual(Internship.objects.count(), 1)

    def test_create_internship_with_stipend(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {**self.valid_payload, 'stipend': 20000.00}
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['stipend'], '20000.00')

    def test_create_internship_student_forbidden(self):
        student_login = self.client.post('/api/auth/login/', {
            'email': 'student@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {student_login.data["access"]}')
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_create_internship_unauthenticated(self):
        response = self.client.post(self.url, self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_internship_missing_title(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {**self.valid_payload}
        del payload['title']
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_internship_missing_location(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        payload = {**self.valid_payload}
        del payload['location']
        response = self.client.post(self.url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InternshipUpdateTests(TestCase):
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
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Engineer Intern',
            description='Build cool stuff',
            location='Remote',
            duration='3 months',
        )
        self.url = f'/api/internships/{self.internship.id}/'
        login_res = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.token = login_res.data['access']

        other_login = self.client.post('/api/auth/login/', {
            'email': 'company2@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.other_token = other_login.data['access']

    def test_update_internship_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(self.url, {'title': 'Updated Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    def test_update_internship_non_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        response = self.client.put(self.url, {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('error', response.data)

    def test_update_internship_unauthenticated(self):
        response = self.client.put(self.url, {'title': 'Hacked Title'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_internship_partial(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.put(self.url, {'location': 'San Francisco'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['location'], 'San Francisco')
        self.assertEqual(response.data['title'], 'Software Engineer Intern')


class InternshipDeleteTests(TestCase):
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
        self.internship = Internship.objects.create(
            company=self.company,
            title='Software Engineer Intern',
            description='Build cool stuff',
            location='Remote',
            duration='3 months',
        )
        self.url = f'/api/internships/{self.internship.id}/'
        login_res = self.client.post('/api/auth/login/', {
            'email': 'company@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.token = login_res.data['access']

        other_login = self.client.post('/api/auth/login/', {
            'email': 'company2@example.com',
            'password': 'StrongPass123!',
        }, format='json')
        self.other_token = other_login.data['access']

    def test_delete_internship_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Internship.objects.count(), 0)

    def test_delete_internship_non_owner_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Internship.objects.count(), 1)

    def test_delete_internship_unauthenticated(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Internship.objects.count(), 1)

    def test_delete_nonexistent_internship(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.delete('/api/internships/999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
