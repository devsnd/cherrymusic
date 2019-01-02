import coreapi
import coreschema
from dataclasses import dataclass
from functools import wraps
from rest_framework.schemas import AutoSchema


@dataclass
class ActionKwarg:
    name: str
    type: type = str
    location: str = 'query'
    required: bool = True
    description: str = ''

    @property
    def title(self):
        return self.name.title()



def action_kwargs(*kwargs):
    '''
    :param kwargs: dictionary mapping the kwarg name to a tuple of location and type,
                   e.g. {'q': (str, 'query')}
    :return: the original function
    '''
    def decorator(func):
        func._schema_kwargs = kwargs
        return func
    return decorator


def _python_type_to_coreschema_cls(type_):
    return {
        str: coreschema.String,
        int: coreschema.Integer,
        float: coreschema.Number,
    }[type_]


class AutoSchemaPlus(AutoSchema):
    def get_link(self, path, method, base_url):
        link = super().get_link(path, method, base_url)
        # now inject the additional parameters from the decorators
        if self.view.action_map:
            action_method_name = self.view.action_map[method.lower()]
            action_method = getattr(self.view, action_method_name)
            if hasattr(action_method, '_schema_kwargs'):
                for action_kwarg in getattr(action_method, '_schema_kwargs'):
                    coreschema_cls = _python_type_to_coreschema_cls(action_kwarg.type)
                    link._fields = tuple(list(link._fields) + [coreapi.Field(
                        name=action_kwarg.name,
                        location=action_kwarg.location,
                        required=action_kwarg.required,
                        schema=coreschema_cls(
                            title=action_kwarg.title,
                            description=action_kwarg.description
                        )
                    )])
        return link
