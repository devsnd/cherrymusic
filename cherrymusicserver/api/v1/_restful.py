import cherrypy
import json

exposed = True

json_in = cherrypy.tools.json_in
json_out = cherrypy.tools.json_out


def jsonify_error_page_handler(status, message, traceback, version):
    cherrypy.response.headers['Content-Type'] = 'application/json'
    return json.dumps({
        'status': "error",
        'notifications': [{'status': 'error', 'message': message}]
    })


def jsonify(func):
    decorated = json_in()(json_out()(func))
    decorated._cp_config.update({'error_page.default': jsonify_error_page_handler})
    return decorated
