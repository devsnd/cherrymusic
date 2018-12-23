import inspect
from django.conf.urls import url
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.db.models import ManyToOneRel, ManyToManyRel, ManyToManyField
from django.http import HttpResponseRedirect


def generate_auto_model_admin(model, hidden_fields=('id',), object_actions=(), **kwargs):
    from django.contrib import admin
    list_display = ['id']
    for field in model._meta.get_fields():
        # do not print the many to one relations in this admin
        if (
                isinstance(field, ManyToOneRel) or
                isinstance(field, ManyToManyRel) or
                isinstance(field, ManyToManyField)
        ):
            continue
        if field.name not in hidden_fields:
            list_display.append(field.name)

    actions = kwargs.pop('actions', [])

    object_action_funcs = {}
    for object_action_name in object_actions:
        def object_action_func(modeladmin, request, queryset):
            for elem in queryset:
                getattr(elem, object_action_name)
        object_action_func.__name__ = object_action_name
        object_action_funcs[object_action_name] = object_action_func

    cls_attrs = {
        'list_display': list_display,
        'actions': [*actions, *object_action_funcs.keys()],
        **object_action_funcs,
    }
    cls_attrs.update(kwargs)
    admincls = type(
        model.__qualname__,
        (admin.ModelAdmin,),
        cls_attrs
    )
    return admincls


def generate_and_register_admin(model, **cls_attrs):
    from django.contrib import admin
    admin.site.register(model, generate_auto_model_admin(model, **cls_attrs))


class ObjectActionAdminMixin:
    def get_actions(self, request):
        actions = super().get_actions(request)
        cls = self.__class__
        for name in getattr(cls, 'object_actions', []):
            # allow setting a tuple for prettier method names
            pretty_name = None
            if isinstance(name, tuple):
                name, pretty_name = name
            if hasattr(cls, name):
                raise ImproperlyConfigured(
                    'The admin %s already has an attribute with the same name '
                    'as object action: %s' % (cls.__name__, name)
                )
            if name in cls.actions:
                raise ImproperlyConfigured(
                    'There is already an action with the same name as the '
                    'object action: %s' % name
                )

            def _closure():  # workaround for pythons weird closures
                _closure_action_name = name

                def func(modeladmin, request, queryset):
                    for elem in queryset:
                        getattr(elem, _closure_action_name)()
                return func
            func = _closure()
            func.__name__ = name

            actions[name] = (
                func, name, pretty_name if pretty_name else name.replace('_', ' ')
            )
        return actions


class ModelActionAdminMixin:
    model_actions = []
    change_list_template = 'utils/admin/class_action_change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(r'^model-action/$', self.model_action_view, name='%s_%s_model_action' % info),
        ] + urls

    def model_action_view(self, request):
        action = request.GET.get('action')
        if action is None or action not in self.__class__.model_actions:
            messages.warning(request, 'Invalid model action: "%s"' % action)
            return HttpResponseRedirect("../")
        pretty_action = action.replace('_', ' ').title()
        try:
            # allow calling either model's classmethods or admin's classmethods
            method = getattr(self.model, action)
        except AttributeError:
            try:
                method = getattr(self, action)
            except AttributeError:
                messages.warning(
                    request, 'Missing classmethod for action "%s"' % pretty_action
                )
                return HttpResponseRedirect("../")
        if not inspect.ismethod(method):
            messages.warning(
                request, 'action %s must be a classmethod!' % pretty_action
            )
        # allow the method to take one argument, the request
        if len(inspect.getargspec(method)[0]) == 2:
            method(request)
        else:
            method()
        messages.info(request, 'Executed action "%s"' % pretty_action)
        return HttpResponseRedirect("../")

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['model_actions'] = [
            {'name': action, 'title': action.replace('_', ' ').title()}
            for action in self.__class__.model_actions
        ]
        return super().changelist_view(request, extra_context)
