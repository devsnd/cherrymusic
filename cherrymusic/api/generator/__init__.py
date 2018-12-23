from collections import defaultdict

from dataclasses import dataclass
from typing import List

typescript_stub = '''
//
//  AUTO-GENERATED API INTERFACE
//
//  To add an endpoint, please implement the endpoint in the server and then
//  regenerate this file by calling:
//
//      make generate_api
//

export module API {

    class Settings {
        static baseUrl: String = '';
        
        static setBaseUrl (baseUrl: String) {
            this.baseUrl = baseUrl;
        }
        
        static getBaseUrl (): String {
            return this.baseUrl;
        }
        
        static async call (method: String, path: String, data?: any) {
            const url = Settings.getBaseUrl() + path;
            let options = {
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

%s
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
        'string': 'String',
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
    call_name: str
    parameters: List[APICallParameter]
    method: str

    @property
    def call_name_camel(self):
        return snake_to_camel_case(self.call_name)

    @property
    def f_string_path(self):
        # use JS style f-strings to do the variable replacement `${var}`
        return f"`{self.path.replace('{', '${')}`"

    def to_typescript(self):
        return f'''
        async {self.call_name_camel} ({' '.join(param.to_typescript() for param in self.parameters)}) {{
            return Settings.call('{self.method}', {self.f_string_path});
        }}
        '''

@dataclass
class APIGroup:
    group_name: str
    api_calls: List[APICall]

    @property
    def group_name_camel(self):
        return snake_to_camel_case(self.group_name).title()

    @property
    def sorted_api_calls(self):
        return sorted(self.api_calls, key=lambda call: call.call_name)

    def to_typescript(self):
        calls = f'''{' '.join(call.to_typescript() for call in self.sorted_api_calls)}'''
        return f'''    class {self.group_name_camel} {{%s
    }}
        ''' % calls

def generate_typescript_api(schema):
    api_groups = defaultdict(list)
    for path, path_spec in schema['paths'].items():
        for method, specs in path_spec.items():
            group_name = specs['tags'][0]  # use the first tag to group the api calls
            call_name = specs['operationId'][len(group_name) + 1:]
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
                call_name=call_name,
                parameters=parameters,
                method=method,
            )
            api_groups[group_name].append(api_call)

    sorted_groups = sorted(
        (
            APIGroup(group_name=name, api_calls=calls)
            for (name, calls) in api_groups.items()
        ),
        key=lambda group: group.group_name
    )
    generated = '\n'.join(
        group.to_typescript() for group in sorted_groups
    )

    return typescript_stub % generated
