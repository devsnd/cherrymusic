from collections import defaultdict

from dataclasses import dataclass
from django import template
from typing import List

from django.template import Template, Context


typescript_template = '''
{% load api_generator %}

//
//  AUTO-GENERATED API INTERFACE
//
//  To add an endpoint, please implement the endpoint in the server and then
//  regenerate this file by calling:
//
//      make generate_api
//

export module API {

    export class Settings {
        static baseUrl: string = '';

        static setBaseUrl (baseUrl: string) {
            this.baseUrl = baseUrl;
        }

        static getBaseUrl (): string {
            return this.baseUrl;
        }

        static async call (method: string, path: string, data?: any) {
            const url = Settings.getBaseUrl() + path;
            let options: any = {
                method: method,
            }
            if (data) {
                options = {...options, body: JSON.stringify(data)};
            }
            const response = await fetch(url, options);
            if (!response.ok) {
                throw new Error(response.statusText)
            }
            return response.json()
        }
    }

    {% for namespace in api_namespaces %}
    export class {{namespace.name | upper_camel_case}} {
        {% for api_call in namespace.api_calls %}static async {{api_call.name | lower_camel_case}} ({% for param in api_call.parameters %}{{param.to_typescript}}{%endfor%}) {
            return Settings.call('{{api_call.method}}', {{api_call.f_string_path}});
        }{% if not forloop.last %}

        {% endif %}{% endfor %}
    }
    {% endfor %}
}
'''


def snake_to_camel_case(snake):
    words = snake.lower().split('_')
    head, rest = words[0], words[1:]
    return head + ''.join(elem.title() for elem in rest)


@dataclass
class APICallParameter:
    name: str
    required: bool
    type_: str

    _typescript_type_mapping = {
        'integer': 'Number',
        'string': 'string',
    }

    @property
    def typescript_type(self):
        try:
            return self.__class__._typescript_type_mapping[self.type_]
        except KeyError:
            return 'UNKNOWN_TYPE'

    @property
    def required_flag(self):
        return '' if self.required else '?'

    @property
    def name_camel(self):
        return snake_to_camel_case(self.name)

    def to_typescript(self):
        return f'{self.name_camel}{self.required_flag}: {self.typescript_type}'

@dataclass
class APICall:
    path: str
    name: str
    parameters: List[APICallParameter]
    method: str

    @property
    def name_camel(self):
        return snake_to_camel_case(self.name)

    @property
    def f_string_path(self):
        # use JS style f-strings to do the variable replacement `${var}`
        return f"`{self.path.replace('{', '${')}`"


@dataclass
class APINamespace:
    name: str
    _api_calls: List[APICall]

    @property
    def api_calls(self):
        return sorted(self._api_calls, key=lambda call: call.name)


def generate_typescript_api(schema):
    api_namespaces = defaultdict(list)
    for path, path_spec in schema['paths'].items():
        for method, specs in path_spec.items():
            namespace_name = specs['tags'][0]  # use the first tag to group the api calls
            call_name = specs['operationId'][len(namespace_name) + 1:]
            parameters = [
                APICallParameter(
                    name=parameter['name'],
                    required=parameter['required'],
                    type_=parameter['schema']['type'],
                )
                for parameter in specs.get('parameters', [])
            ]
            api_call = APICall(
                path=path,
                name=call_name,
                parameters=parameters,
                method=method,
            )
            api_namespaces[namespace_name].append(api_call)

    # sort namespaces by name so that the template is rendered reproducable
    api_namespaces = sorted(
        (
            APINamespace(name=name, _api_calls=calls)
            for (name, calls) in api_namespaces.items()
        ),
        key=lambda group: group.name
    )

    t = Template(typescript_template)
    c = Context({"api_namespaces": api_namespaces})
    return t.render(c)
