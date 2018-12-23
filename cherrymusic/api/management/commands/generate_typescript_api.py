import yaml
from django.core.management import BaseCommand

from api.generator import generate_typescript_api


class Command(BaseCommand):
    help = 'Generates the typescript API for the client'

    def add_arguments(self, parser):
        parser.add_argument('schema-yaml', nargs=1, type=str)
        parser.add_argument('output', nargs=1, type=str)

    def handle(self, *args, **options):
        schema_path = options['schema-yaml'][0]
        output_path = options['output'][0]
        with open(schema_path, 'r', encoding='utf-8') as fh:
            schema = yaml.load(fh.read())
        api_ts = generate_typescript_api(schema)
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(api_ts)
