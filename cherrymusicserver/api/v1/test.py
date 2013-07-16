from cherrymusicserver.api.v1._restful import *


@json_out()              # auto-converts return value to JSON
def GET(*args, **params):
    return "test.GET", args, params
