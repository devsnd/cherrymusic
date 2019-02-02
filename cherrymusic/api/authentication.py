from rest_framework.authentication import TokenAuthentication


class TokenHTTPAuthentication(TokenAuthentication):
    def authenticate(self, request):
        token = None
        if request._request.method == 'GET':
            token = request._request.GET.get('authtoken', '')
        elif request._request.method in ['POST', 'PUT']:
            token = request.data.get('authtoken', '')
        return self.authenticate_credentials(token)

