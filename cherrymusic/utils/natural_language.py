import re

re_special_chars = re.compile('[^\w\s]')

def normalize_name(name):
    return re_special_chars.sub(' ', name).lower().strip()
