import pytest
from werkzeug.exceptions import Forbidden

from flask_allows import Allows, Permission


def test_Permission_provide_ident(app, member, ismember):
    Allows(app=app)

    p = Permission(ismember, identity=member)

    assert p.identity is member


def test_Permission_as_bool(app, member, always):
    Allows(app=app, identity_loader=lambda: member)
    p = Permission(always)

    with app.app_context():
        result = bool(p)

    assert result and always.called_with["user"] is member


def test_Permission_bool_doesnt_raise(app, member, never):
    Allows(app=app, identity_loader=lambda: member)
    p = Permission(never)

    with app.app_context():
        result = bool(p)

    assert not result and never.called_with["user"] is member


def test_Permission_allowed_context(app, member, always):
    Allows(app=app, identity_loader=lambda: member)

    allowed = False
    p = Permission(always)

    with app.app_context(), p:
        allowed = True

    assert allowed


def test_Permission_forbidden_context(app, member, never):
    Allows(app=app, identity_loader=lambda: member)
    p = Permission(never)

    with app.app_context():
        with pytest.raises(Forbidden) as excinfo:
            with p:
                pass

    assert excinfo.value.code == 403


def test_Permission_on_fail(app, member, never):
    Allows(app=app, identity_loader=lambda: member)

    def on_fail(*a, **k):
        on_fail.failed = True

    on_fail.failed = False
    p = Permission(never, on_fail=on_fail)

    with app.app_context():

        with pytest.raises(Forbidden):
            with p:
                pass
    assert on_fail.failed
