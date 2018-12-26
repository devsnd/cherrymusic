import json
import logging
import re

logger = logging.getLogger(__name__)


def get_js_object_as_dict_after_marker(marker, txt, max_size=512 * 1024):
    """
    this function makes it easy to parse ugly javascript parts from html pages. just specify the
    marker at which the js object begins and this function will determine when the object ends and
    transform it into a python dict.

    e.g.
    html = '<script>my_obj = {... deeply nested object ...}; more_javascript();'
    get_js_object_as_dict_after_marker('my_obj = ', html)

    Args:
        marker:
        txt:

    Returns:

    """
    start_pos = txt.index(marker) + len(marker)
    txt = txt[start_pos:]
    stack = []

    debug = False

    pos = -1
    while pos < len(txt):
        pos += 1
        c = txt[pos]
        if pos > max_size:
            raise IndexError('Max size exceeeded, stopped parsing')

        is_text = stack and stack[-1] == '"'
        if is_text:
            if c == '\\':  # the next letter is escaped so we skip it completely in this parser
                pos += 1
                continue

            if c == '"':
                if stack[-1] != '"':
                    msg = 'error parsing, unmatching double quotes!'
                    logger.error(msg, extra={
                        'parser_stack': stack,
                        'data': txt
                    })
                    raise ValueError(msg)
                stack.pop(-1)
                if debug:
                    print(pos, stack)
                continue
            else:
                continue  # read over strings

        if c == '"':
            stack.append(c)
            if debug:
                print(pos, stack)
            continue

        if c == '{':
            stack.append(c)
            if debug:
                print(pos, stack)
            continue

        if c == '}':
            if stack[-1] != '{':
                msg = 'error parsing, unmatching curly braces!'
                logger.error(msg, extra={
                    'parser_stack': stack,
                    'data': txt
                })
                raise ValueError(msg)
            stack.pop(-1)
            if debug:
                print(pos, stack)
            continue

        if not stack and pos > 0:
            # ensure that all the keys in the object are double quoted so we can parse it using the json parser
            jsobject = re.sub('([\{,])\s*?(\w+)(:)', '\\1"\\2"\\3', txt[:pos])
            return json.loads(jsobject)

