from django.contrib.auth.models import AbstractUser
from storage.models import File
from utils.models import BaseModel


class User(AbstractUser, BaseModel):
    def generate_auth_token(self):
        from rest_framework.authtoken.models import Token
        return Token.objects.create(user=self)




