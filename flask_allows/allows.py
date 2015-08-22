from functools import wraps
from flask import request, current_app
from werkzeug.exceptions import Forbidden
from werkzeug import LocalProxy

class Allows(object):
    """Allows gives you the ability to impose identity requirements on routes
    in your Flask application. Simply initialize it, create some requirements
    and begin decoratoring your routes.

        .. code-block:: python

        from flask import Flask
        from flask_allows import Allows, Requirement
        from flask_login import current_user

        app = Flask(__name__)
        allows = Allows(app=app, identity_loader=lambda: current_user)

        class IsAdmin(Requirement):
            def requires(self, user, request):
                return user.permissions.get('admin')

        @app.route('/admin')
        @allows.requires(IsAdmin())
        def admin_index():
            return "Welcome to the super secret club"


    Allows supports any callable that accepts an identity and a Flask request
    as arguments and returns a boolean as a response. Allows ships with a
    Requirement class as well as a ConditionalRequirement class as helpers for
    more complex requirements.

    By default, if a requirement isn't met, a werkzeug Forbidden exception is
    raised, but this can be overriden by providing an exception to the `throws`
    keyword when creating an instance. This can be a class or a particular
    instance of an exception.


        .. code-block:: python

        Allows(throws=MyForbidden)
        Allows(throws=MyForbidden("You can't sit with us"))

    Allows is unopinionated about how users and identities are stored, however
    it does want a function to call to get at whatever the user is. This can
    be provided in the initializer.

        .. code-block:: python

        allows = Allows(identity_loader=lambda: g.user)

    Or provided later via a decorator:

        .. code-block:: python

        allows = Allows()

        @allows.identity_loader
        def load_user():
            return g.user
    """
    def __init__(self, app=None, identity_loader=None, throws=Forbidden):
        self._identity_loader = identity_loader
        self.throws = throws

        if app:
            self.init_app(app)

    def init_app(self, app):
        if not hasattr(app, 'extensions'):  # pragma: no cover
            app.extensions = {}
        app.extensions['allows'] = self

    def requires(self, *requirements, **opts):
        """Decorator to enforce requirements on routes

            allows = Allows(app)

            @app.route('/<username>/edit', methods=['GET', 'POST'])
            @allows.requires(IsAuthenticated(), Or(IsSameUser(), CanEditUser()))
            def edit_user(username):
                ...

        :param requirements iterable: Collection of requirements
        to impose on view
        :param throws optional: Exception to throw for this route, if provided
        it takes precedence over the exception stored on the instance
        """
        throws = opts.get('throws', self.throws)

        def decorator(f):
            @wraps(f)
            def allower(*args, **kwargs):
                if self.fulfill(requirements):
                    return f(*args, **kwargs)
                else:
                    raise throws
            return allower
        return decorator

    def identity_loader(self, f):
        "Provides an identity loader for the instance"
        self._identity_loader = f
        return f

    def fulfill(self, requirements, identity=None):
        "Runs each requirement until one is not fulfilled"
        identity = identity or self._identity_loader()
        return all(r(identity, request) for r in requirements)


def __get_allows():
    "Internal helper"
    try:
        return current_app.extensions['allows']
    except (AttributeError, KeyError):
        raise RuntimeError("Flask-Allows not configured against current app")

_allows = LocalProxy(__get_allows, name="flask-allows")
