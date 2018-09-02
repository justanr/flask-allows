import pytest
from flask.views import MethodView, View
from werkzeug.exceptions import Forbidden

from flask_allows import Allows, requires


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


def test_requires_works_as_cbv_decorator(app, ismember, guest):
    class IsMemberView(View):
        decorators = [requires(ismember)]

    Allows(app=app, identity_loader=lambda: guest)

    with pytest.raises(Forbidden):
        with app.app_context():
            IsMemberView.as_view("memberonly")()


def test_requires_works_as_method_decorator(app, ismember, guest):
    class MembersCanPost(MethodView):
        @requires(ismember)
        def post(self):
            return "hello"

    Allows(app=app, identity_loader=lambda: guest)
    context = app.test_request_context("/", method="POST")

    with pytest.raises(Forbidden), app.app_context(), context:
        MembersCanPost.as_view("memberonly")()


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
