from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render

# Create your views here.
from django.views.generic import TemplateView, FormView, View


class MainView(TemplateView):
    template_name = 'client/main.html'

    def get_context_data(self, **kwargs):
        return {}



class LoginView(TemplateView):
    template_name = 'client/login.html'
    form_class = AuthenticationForm

    def get_success_url(self):
        return self.request.REQUEST.get('next', '/')

    def post(self, request, *args, **kwargs):
        form = self.form_class(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                if user.is_active:
                    print('active')
                    login(request, user)
                    return HttpResponseRedirect(reverse('main-view'))
        else:
            print(form.error_messages)

        return HttpResponseRedirect(reverse('login-view'))
