import pytest
from flask import Response
from werkzeug.exceptions import Forbidden

from flask_allows import Allows
from flask_allows.overrides import current_overrides


def test_warns_about_request_deprecation_with_old_style_requirement(member):
    import warnings

    allows = Allows(identity_loader=lambda: member)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        allows.fulfill([lambda u, r: True])
        warnings.simplefilter("default", DeprecationWarning)

    assert len(w) == 1
    assert issubclass(w[0].category, DeprecationWarning)
    assert "Passing request to requirements is now deprecated" in str(w[0].message)


def test_Allows_defaults():
    allows = Allows()
    assert allows._identity_loader is None and allows.throws is Forbidden


def test_Allows_config_with_app(app):
    allows = Allows(app)
    assert hasattr(app, "extensions") and allows is app.extensions["allows"]


def test_Allows_init_app(app):
    allows = Allows()
    assert app.extensions == {}

    allows.init_app(app)
    assert hasattr(app, "extensions") and allows is app.extensions["allows"]


def test_Allows_identity_loader_on_init(member):
    ident = lambda: member  # noqa
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
    assert always.called_with == {"user": member, "request": request}


def test_Allows_fulfill_false(member, never, request):
    allows = Allows(identity_loader=lambda: member)
    assert not allows.fulfill([never])


def test_Allows_fulfill_ident_override(member, guest, spy):
    allows = Allows(identity_loader=lambda: guest)
    allows.fulfill([spy], identity=member)
    assert spy.called_with["user"] is member


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

    @allows.requires(atleastmod, throws=MyForbid("Go away"))
    def stub():
        pass

    with pytest.raises(MyForbid) as excinfo:
        stub()

    assert "Go away" == excinfo.value.description


def test_allows_on_fail(member, atleastmod):
    allows = Allows(
        identity_loader=lambda: member, on_fail=lambda *a, **k: "I've failed"
    )

    @allows.requires(atleastmod)
    def stub():
        pass

    assert stub() == "I've failed"


def test_allows_makes_on_fail_callable(member, atleastmod):
    allows = Allows(identity_loader=lambda: member, on_fail="I've failed")

    @allows.requires(atleastmod)
    def stub():
        pass

    assert stub() == "I've failed"


def test_allows_on_fail_override_at_decoration(member, atleastmod):
    allows = Allows(identity_loader=lambda: member)

    @allows.requires(atleastmod, on_fail=lambda *a, **k: "Overridden failure")
    def stub():
        pass

    assert stub() == "Overridden failure"


def test_allows_on_fail_returning_none_raises(member, atleastmod):
    allows = Allows(on_fail=lambda *a, **k: None, identity_loader=lambda: member)

    @allows.requires(atleastmod)
    def stub():
        pass

    with pytest.raises(Forbidden):
        stub()


def test_allows_can_call_requirements_with_old_and_new_style_arguments(member):
    allows = Allows(identity_loader=lambda: member)

    def new_style(user):
        return True

    def old_style(user, request):
        return True

    assert allows.fulfill([new_style, old_style])


def test_allows_cleans_up_override_contexts_in_after_request(app, member, never):
    allows = Allows(app, identity_loader=lambda: member)

    # need to route a request for this test so the whole before/after request
    # cycle is invoked

    @app.route("/")
    def index():
        assert allows.overrides.current.is_overridden(never)
        return Response("...")

    @app.before_request
    def disable_never(*a, **k):
        current_overrides.add(never)

    with app.test_request_context("/"):
        app.preprocess_request()
        result = index()
        app.process_response(result)

    assert allows.overrides.current is None
