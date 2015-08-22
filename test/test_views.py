from flask_allows import Allows, requires, PermissionedView
from werkzeug.exceptions import Forbidden
import pytest


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
