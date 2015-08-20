import pytest
from flask_allows import Allows
from flask_allows.allows import _get_allows
from werkzeug.exceptions import Forbidden


def test_get_allows_raises_runtime(app):
    with app.app_context():
        with pytest.raises(RuntimeError) as excinfo:
            _get_allows()

    assert "Flask-Allows not configured against current app" == str(excinfo.value)


def test_get_allows(app):
    allows = Allows(app)

    with app.app_context():
        got = _get_allows()

    assert allows is got


def test_get_allows_retrieves_subclass(app):
    class SubAllows(Allows):
        pass

    allows = SubAllows(app)

    with app.app_context():
        got = _get_allows()

    assert got is allows


def test_Allows_defaults():
    allows = Allows()
    assert allows._identity_loader is None and allows.throws is Forbidden


def test_Allows_config_with_app(app):
    allows = Allows(app)
    assert hasattr(app, 'extensions') and allows is app.extensions['allows']


def test_Allows_init_app(app):
    allows = Allows()
    assert app.extensions == {}

    allows.init_app(app)
    assert hasattr(app, 'extensions') and allows is app.extensions['allows']


def test_Allows_identity_loader_on_init(member):
    ident = lambda: member
    allows = Allows(identity_loader=ident)
    assert allows._identity_loader is ident


def test_Allows_custom_throws():
    myforbid = Forbidden()
    allows = Allows(throws=myforbid)

    assert allows.throws is myforbid


def test_Allows_identity_loader_func(member):
    allows = Allows()

    @allows.identity_loader
    def ident():
        return member

    assert allows._identity_loader is ident and allows._identity_loader() is member


def test_Allows_fulfill_true(member, always, request):
    allows = Allows(identity_loader=lambda: member)
    assert allows.fulfill([always])
    assert always.called_with == {'user': member, 'request': request}


def test_Allows_fulfill_false(member, never, request):
    allows = Allows(identity_loader=lambda: member)
    assert not allows.fulfill([never])


def test_Allows_fulfill_ident_override(member, guest, spy):
    allows = Allows(identity_loader=lambda: guest)
    allows.fulfill([spy], identity=member)
    assert spy.called_with['user'] is member


def test_allows_requires(member, ismember):
    allows = Allows(identity_loader=lambda: member)

    @allows.requires(ismember)
    def stub():
        return True

    assert stub()


def test_allows_requires_throws(member, atleastmod):
    allows = Allows(identity_loader=lambda: member)

    @allows.requires(atleastmod)
    def stub():
        return True

    with pytest.raises(Forbidden) as excinfo:
        stub()

    assert excinfo.value.code == 403


def test_allows_requires_throws_override(member, atleastmod):
    class MyForbid(Forbidden):
        pass

    allows = Allows(identity_loader=lambda: member)

    @allows.requires(atleastmod, throws=MyForbid('Go away'))
    def stub():
        pass

    with pytest.raises(MyForbid) as excinfo:
        stub()

    assert 'Go away' == excinfo.value.description
