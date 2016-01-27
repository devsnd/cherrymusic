from django.contrib.auth import get_user_model
from django.utils import timezone

from datetime import timedelta

from .models import File


class ServerStatus(object):
    @classmethod
    def get_latest(cls):
        User = get_user_model()
        last_login_active_date = timezone.now() - timedelta(hours=1)

        return {
            'indexed_files': File.objects.count(),
            'meta_indexed_files': File.objects.filter(meta_index_date__isnull=False).count(),
            'active_users': User.objects.filter(last_login__gt=last_login_active_date).count(),
        }