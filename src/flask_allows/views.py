from .permission import Permission
from flask.views import View, MethodView
from functools import wraps


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
        allower = requires(*cls.requirements)
        view = allower(super(PermissionedView, cls).as_view(name, *cls_args, **cls_kwargs))
        view.requirements = cls.requirements
        return view


class PermissionedMethodView(PermissionedView, MethodView):
    pass
