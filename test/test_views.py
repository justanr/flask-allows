from flask_allows import Allows, requires, PermissionedView
from flask.views import View, MethodView
from werkzeug.exceptions import Forbidden
import pytest
import warnings


def test_requires_allows(app, member, ismember):
    Allows(app=app, identity_loader=lambda: member)

    @requires(ismember)
    def stub():
        return True

    with app.app_context():
        assert stub()


def test_requires_fails(app, guest, ismember):
    Allows(app=app, identity_loader=lambda: guest)

    @requires(ismember)
    def stub():
        pass

    with pytest.raises(Forbidden):
        with app.app_context():
            stub()


def test_PermissionedView_as_view(ismember):
    class IsMemberView(PermissionedView):
        requirements = [ismember]

    assert IsMemberView.as_view('memberonly').requirements == \
        IsMemberView.requirements


def test_PermissionedView_allows(app, ismember, member):
    class IsMemberView(PermissionedView):
        requirements = [ismember]

        def dispatch_request(self):
            return True

    Allows(app=app, identity_loader=lambda: member)

    with app.app_context():
        assert IsMemberView.as_view('memberonly')()


def test_PermissionedView_fails(app, ismember, guest):
    class IsMemberView(PermissionedView):
        requirements = [ismember]

    Allows(app=app, identity_loader=lambda: guest)

    with pytest.raises(Forbidden):
        with app.app_context():
            IsMemberView.as_view('memberonly')()


def test_View_requirements_is_depercated(ismember):
    class SomeView(PermissionedView):
        requirements = [ismember]

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter('always', DeprecationWarning)
        SomeView.as_view('some_view')
        warnings.simplefilter('default', DeprecationWarning)

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "PermissionedView is deprecated" in str(w[0].message)


def test_requires_works_as_cbv_decorator(app, ismember, guest):
    class IsMemberView(View):
        decorators = [requires(ismember)]

    Allows(app=app, identity_loader=lambda: guest)

    with pytest.raises(Forbidden):
        with app.app_context():
            IsMemberView.as_view('memberonly')()


def test_requires_works_as_method_decorator(app, ismember, guest):
    class MembersCanPost(MethodView):
        @requires(ismember)
        def post(self):
            return 'hello'

    Allows(app=app, identity_loader=lambda: guest)
    context = app.test_request_context('/', method='POST')

    with pytest.raises(Forbidden), app.app_context(), context:
        MembersCanPost.as_view('memberonly')()


def test_requires_on_fail_local_override(app, ismember, guest):
    @requires(ismember, on_fail="I've failed")
    def stub():
        pass

    Allows(app=app, identity_loader=lambda: guest)

    with app.app_context():
        assert stub() == "I've failed"


def test_requires_defaults_to_allows_override(app, ismember, guest):
    @requires(ismember)
    def stub():
        pass

    Allows(app=app, on_fail="I've failed", identity_loader=lambda: guest)

    with app.app_context():
        assert stub() == "I've failed"


def test_requires_on_fail_returning_none_raises(app, ismember, guest):
    @requires(ismember)
    def stub():
        pass

    Allows(app=app, on_fail=lambda *a, **k: None, identity_loader=lambda: guest)

    with pytest.raises(Forbidden), app.app_context():
        stub()
