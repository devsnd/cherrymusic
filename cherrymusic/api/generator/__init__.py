from collections import defaultdict

from dataclasses import dataclass
from django import template
from typing import List

from django.template import Template, Context


typescript_template = '''{% load api_generator %}
//
//  AUTO-GENERATED API INTERFACE
//
//  To add an endpoint, please implement the endpoint in the server and then
//  regenerate this file by calling:
//
//      make generate_api
//

import * as _ from 'lodash';
import {dict} from "@/common/utils";


export abstract class APIEndpoint {
}


type HTTPMethod = 'get' | 'post' | 'delete' | 'patch' | 'put';


export class Settings {
    static baseUrl: string = '';
    private static authtoken: string | null = null;

    static setBaseUrl (baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    static getBaseUrl (): string {
        return this.baseUrl;
    }
    
    static setAuthtoken (authtoken: string) {
        this.authtoken = authtoken;
    }
    
    static getAuthToken (): string | null {
        return this.authtoken;
    }
    
    static encodeGetParams (params: {[key:string]: string}): string {
      return (
          Object.entries(params)
          .map(([key, value]) => (key + '=' + encodeURIComponent(value)))
          .join("&")
      );
    }

    static async call (method: HTTPMethod, path: string, data?: any) {
        let url = Settings.getBaseUrl() + path;
        let options: any = {
            method: method,
            headers: new Headers({'content-type': 'application/json'}),
        };
        if (data === undefined) {
            data = {};
        }
        if (Settings.authtoken !== null) {
            data.authtoken = Settings.authtoken;
        }
        
        // map all calls to snake case
        data = dict(Object.entries(data).map((elem: any) => [_.snakeCase(elem[0]), elem[1]]));

        if (method === 'post') {
            options = {...options, body: JSON.stringify(data)};
        } else if (method === 'get') {
            url = url + '?' + Settings.encodeGetParams(data);        
        }

        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(response.statusText)
        }
        return response.json()
    }
}

// generate the argument types for each api call which
{% for namespace in api_namespaces %}\
{% for api_call in namespace.api_calls %}
type {{namespace.name | upper_camel_case}}{{api_call.name | upper_camel_case}}Args = {
{% for param in api_call.query_parameters %}    {{param.name}}{% if not param.required %}?{% endif %}: {{param.typescript_type}},
{% endfor %}\
}
{% endfor %}
\
export class {{namespace.name | upper_camel_case}} implements APIEndpoint {
{% for api_call in namespace.api_calls %}\
    static async {{api_call.name | lower_camel_case}} \
(\
{% for param in api_call.path_parameters %}\
{{param.name}}{% if not param.required %}?{% endif %}: {{param.typescript_type}}{% if not forloop.last %}, {% endif %}\
{% endfor %}\
{% if api_call.path_parameters %}, {% endif %}\
params?: {{namespace.name | upper_camel_case}}{{api_call.name | upper_camel_case}}Args) {
        return Settings.call('{{api_call.method}}', {{api_call.f_string_path}}, params);
    }\
{% if not forloop.last %}

{% endif %}{% endfor %}
}
{% endfor %}

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
    in_: str

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
    query_parameters: List[APICallParameter]
    path_parameters: List[APICallParameter]
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
            query_parameters = [
                APICallParameter(
                    in_=parameter['in'],
                    name=parameter['name'],
                    required=parameter.get('required', False),
                    type_=parameter['schema']['type'],
                )
                for parameter in specs.get('parameters', [])
                if parameter['in'] == 'query'
            ]
            path_parameters = [
                APICallParameter(
                    in_=parameter['in'],
                    name=parameter['name'],
                    required=parameter.get('required', False),
                    type_=parameter['schema']['type'],
                )
                for parameter in specs.get('parameters', [])
                if parameter['in'] == 'path'
            ]
            api_call = APICall(
                path=path,
                name=call_name,
                query_parameters=query_parameters,
                path_parameters=path_parameters,
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
