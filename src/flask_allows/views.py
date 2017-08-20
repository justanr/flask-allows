from .permission import Permission
from flask.views import View, MethodView
from functools import wraps
import warnings


def requires(*requirements, **opts):
    def decorator(f):
        @wraps(f)
        def allower(*args, **kwargs):
            with Permission(*requirements, **opts):
                return f(*args, **kwargs)
        return allower
    return decorator


class PermissionedView(View):
    requirements = ()

    @classmethod
    def as_view(cls, name, *cls_args, **cls_kwargs):
        view = super(PermissionedView, cls).as_view(name, *cls_args, **cls_kwargs)

        if cls.requirements:
            warnings.warn(
                "Implicit decoration through the requirements attribute is depercated"
                "Place allows.requires(...) into the list of view decorators instead",
                DeprecationWarning,
                stacklevel=2
            )

            view = requires(*cls.requirements)(view)

        view.requirements = cls.requirements
        return view


class PermissionedMethodView(PermissionedView, MethodView):
    pass
