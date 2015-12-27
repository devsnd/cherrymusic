from django.conf.urls import include, url
from django.contrib import admin

from cherrymusic.apps.core.models import User
from cherrymusic.apps.storage.models import Directory

base_dir = Directory(path='/usr/src/app/music')
if len(Directory.objects.all())== 0:
    base_dir.save(is_basedir=True)
    user, created = User.objects.get_or_create(username='admin', email='Admin@admin.com')
    user.is_staff = user.is_superuser = True
    user.set_password('admin')
    user.save()

urlpatterns = [
    # Examples:
    # url(r'^$', 'cherrymusic.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('cherrymusic.apps.api.urls', namespace='rest_framework')),
    url(r'^', include('cherrymusic.apps.client.urls')),

]

