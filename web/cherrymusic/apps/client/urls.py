from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from . import views

urlpatterns = patterns(
    '',
    url(r'^$', login_required(views.MainView.as_view()), name='main_view'),
    url(r'^accounts/login/$', views.LoginView.as_view(), name='login_view'),
)