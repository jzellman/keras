def basic_auth(realm, username, password):
    class HTTPBasic(object):
        "HTTP Basic authentication protocol"
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            def repl_start_response(status, headers, exc_info=None):
                if status.startswith('401'):
                    remove_header(headers, 'WWW-Authenticate')
                    headers.append(('WWW-Authenticate',
                                    'Basic realm="%s"' % realm))
                return start_response(status, headers)

            auth = environ.get('HTTP_AUTHORIZATION')
            if auth:
                scheme, data = auth.split(None, 1)
                assert scheme.lower() == 'basic'
                u, p = data.decode('base64').split(':', 1)
                if u != username or p != password:
                    return self.bad_auth(environ, start_response)
                environ['REMOTE_USER'] = u
                del environ['HTTP_AUTHORIZATION']
                return self.app(environ, repl_start_response)
            else:
                return self.bad_auth(environ, start_response)

        def bad_auth(self, environ, start_response):
            body = 'Please authenticate'
            headers = [
                ('content-type', 'text/plain'),
                ('content-length', str(len(body))),
                ('WWW-Authenticate', 'Basic realm="%s"' % realm)]
            start_response('401 Unauthorized', headers)
            return [body]
    return HTTPBasic


def remove_header(headers, name):
    for header in headers:
        if header[0].lower() == name.lower():
            headers.remove(header)
            break
