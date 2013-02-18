import sys

if sys.version_info < (3,0):
    import urllib as ul
    unquote = ul.unquote
    quote = ul.quote
    from urlparse import urlparse
