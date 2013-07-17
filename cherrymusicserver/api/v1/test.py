from cherrymusicserver.api.v1._restful import *


@jsonify
def GET(*args, **params):
    return "test.GET", args, params
