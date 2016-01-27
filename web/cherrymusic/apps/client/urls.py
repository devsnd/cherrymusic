from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', login_required(views.MainView.as_view(), login_url=None), name='main-view'),
    url(r'^accounts/login/$', views.LoginView.as_view(), name='login-view'),
)