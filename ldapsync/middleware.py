from django.contrib.auth.middleware import RemoteUserMiddleware as _RemoteUserMiddleware

class PersistentRemoteUserMiddleware(_RemoteUserMiddleware):
    """
    This middleware can be used instead of Django's RemoteUserMiddleware when
    a callback URL is used for authenticating remote users.
    """
    force_logout_if_no_header = False
