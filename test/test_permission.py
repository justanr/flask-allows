from flask_allows import Permission, Allows
from werkzeug.exceptions import Forbidden
import pytest


def test_Permission_init(app, ismember):
    allows = Allows(app=app)

    with app.app_context():
        p = Permission(ismember)

    assert (p.ext is allows and p.requirements == (ismember,)
            and p.throws is Forbidden and p.identity is None)


def test_Permission_provide_ident(app, member, ismember):
    Allows(app=app)

    with app.app_context():
        p = Permission(ismember, identity=member)

    assert p.identity is member


def test_Permission_provide_exception(app, member, ismember):
    Allows(app=app)

    class MyForbid(Forbidden):
        pass

    with app.app_context():
        p = Permission(ismember, throws=MyForbid("Nope"))

    assert isinstance(p.throws, MyForbid) and p.throws.description == "Nope"


def test_Permission_as_bool(app, member, always):
    Allows(app=app, identity_loader=lambda: member)

    with app.app_context():
        p = Permission(always)

    assert p and always.called_with['user'] is member


def test_Permission_bool_doesnt_raise(app, member, never):
    Allows(app=app, identity_loader=lambda: member)

    with app.app_context():
        p = Permission(never)

    assert not p and never.called_with['user'] is member


def test_Permission_allowed_context(app, member, always):
    Allows(app=app, identity_loader=lambda: member)

    allowed = False

    with app.app_context():
        p = Permission(always)

    with p:
        allowed = True

    assert allowed


def test_Permission_forbidden_context(app, member, never):
    Allows(app=app, identity_loader=lambda: member)

    with app.app_context():
        p = Permission(never)

    with pytest.raises(Forbidden) as excinfo:
        with p:
            pass

    assert excinfo.value.code == 403
