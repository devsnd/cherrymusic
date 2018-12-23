from django.contrib import admin

from utils.autoadmin import ObjectActionAdminMixin
from .models import User

@admin.register(User)
class UserAdmin(ObjectActionAdminMixin, admin.ModelAdmin):
    list_display = [
        'id',
        'username',
        'first_name',
        'last_name',
        'email',
        'is_staff',
        'is_active',
        'date_joined',
        '_auth_token',
    ]

    object_actions = [
        'generate_auth_token'
    ]

    def _auth_token(self, obj):
        from rest_framework.authtoken.models import Token
        token = Token.objects.filter(user=obj).first()
        if token:
            return token.key

