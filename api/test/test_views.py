import email
from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase, force_authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token

import secrets

UserModel = get_user_model()

class UserRegisterListTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        #Create a Superuser account
        cls.superuser = UserModel.objects.create_superuser(
            email='superuser@email.com',
            password='superuser',
        )
        #create a Staff account
        cls.staffuser = UserModel.objects.create_staffuser(
            email= 'staffuser@email.com',
            password='staffuser',
            is_staff=True,
        )
        
        #create 2 normal useraccounts
        cls.normaluser = UserModel.objects.create_user(
            email= 'normaluser@email.com',
            password='normaluser',
        )
        cls.normaluser2 = UserModel.objects.create_user(
            email= 'normaluser2@email.com',
            password='normaluser2',
        )

    def test_user_registration(self):
        user_data = {
            'email':"user@email.com",
            'first_name':'Foo',
            'Last_name': 'Bar',
            'password': secrets.token_urlsafe(10), #create random strong
        }
        user_data['password2'] = user_data['password']

        #user-list endpoint will be the same as user-create endpoint
        create_user_endpoint = reverse("api:user-list")
        response = self.client.post(create_user_endpoint, data= user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response_fields = set(response.json())
        self.assertEqual(response_fields, {'email', 'first_name', 'last_name'})

    def test_only_admin_can_view_user_list(self):
        #normal user can't access it
        self.client.force_authenticate(user=self.normaluser)
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        #staff can access it
        self.client.force_authenticate(user=self.staffuser)
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #superuser can access it
        self.client.force_authenticate(user=self.superuser)
        response = self.client.get(reverse('api:user-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def tesst_any_user_can_view_user_details(self):
        user_details_endpoint = reverse('api:user-detail', kwargs={"pk"})

        #owner can view details
        self.client.force_authenticate(user=self.normaluser)
        response = self.client.get(user_details_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        #other authenticated user can edit or view detail
        self.client.force_authenticate(user=self.normaluser2)
        response = self.client.get(user_details_endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_user_or_superuser_can_edit_userdetails(self):
        user_details_endpoint = reverse('api:user-detail', kwargs={"pk:"})

        #owner can edit details

        self.client.force_authenticate(user=self.normaluser)
        response = self.client.patch(user_details_endpoint, data={"slug"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.normaluser.refresh_frm_db()
        self.assertEqual(self.normaluser.slug, 'normaluser-slug')

        #Admin can't edit
        self.client.force_authenticate(user=self.staffuser)
        response = self.client.patch(user_details_endpoint, data={"slug"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.normaluser.refresh_frm_db()
        self.assertEqual(self.normaluser.slug, 'normaluser-slug')

        #Superuser can't edit
        self.client.force_authenticate(user=self.staffuser)
        response = self.client.patch(user_details_endpoint, data={"slug"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.normaluser.refresh_frm_db()
        self.assertEqual(self.normaluser.slug, 'superuser-slug')

    def test_user_can_get_token(self):
        get_token_endpoint = reverse('api:get_token')
        response = self.client.post(get_token_endpoint, data={"username"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        received_token = response.json()["token"]
        token= Token.objects.get(user=self.normaluser)
        self.assertEqual(received_token, str(token))
