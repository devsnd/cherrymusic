from django import template

register = template.Library()


def snake_to_camel_case(snake):
    words = snake.lower().split('_')
    head, rest = words[0], words[1:]
    return head + ''.join(elem.title() for elem in rest)


@register.filter()
def lower_camel_case(value):
    return snake_to_camel_case(value)


@register.filter()
def upper_camel_case(value):
    return snake_to_camel_case(value).title()
