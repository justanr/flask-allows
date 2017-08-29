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
        warnings.warn(
            "PermissionedView is deprecated and will be removed in 0.6. Use either requires(...)"
            "or allows.requires(...) in the decorators attribute of View or MethodView.",
            DeprecationWarning,
            stacklevel=2
        )

        view = super(PermissionedView, cls).as_view(name, *cls_args, **cls_kwargs)

        if cls.requirements:
            view = requires(*cls.requirements)(view)

        view.requirements = cls.requirements
        return view


class PermissionedMethodView(PermissionedView, MethodView):
    pass
