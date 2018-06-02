import json
import operator

import pytest
from flask import Blueprint, Flask, g, jsonify, request
from flask.views import MethodView
from flask_allows import (
    Additional,
    Allows,
    And,
    C,
    Not,
    Or,
    Override,
    Permission,
    Requirement,
    exempt_from_requirements,
    guard_blueprint,
    requires,
)
from flask_allows.additional import _additional_ctx_stack
from flask_allows.overrides import _override_ctx_stack

pytestmark = pytest.mark.integration

# This is a whole bunch of setup for the integration tests
# route registrations, user setup, etc
# if you're not interested in this skip to the comment
# THIS IS WHERE THE TESTS BEGIN


class User(object):

    def __init__(self, username, userlevel, *permissions):
        self.username = username
        self.permissions = frozenset(permissions)
        self.userlevel = userlevel

    def has_permission(self, permission):
        return permission in self.permissions

    def __repr__(self):
        return "User({}, {}, {!r})".format(
            self.username, self.userlevel, self.permissions
        )


class AuthLevels:
    banned = "banned"
    guest = "guest"
    user = "user"
    admin = "admin"
    staff = "staff"


users = {
    "banned": User("Brian", AuthLevels.banned),
    "guest": User("George", AuthLevels.guest, "view"),
    "user": User("Ulric", AuthLevels.user, "view", "reply"),
    "admin": User("Adam", AuthLevels.admin, "view", "reply", "edit", "ban"),
    "staff": User(
        "Seth", AuthLevels.staff, "view", "reply", "edit", "ban", "promote"
    ),
}


app = Flask(__name__)
# explicitly turn these off, act like we're the real thing
app.testing = False
app.debug = False


# register this first so we sandwich the extension's before/after
# wouldn't check this in a real application, but we're trying to
# surface corner cases
@app.after_request
@app.before_request
def ensure_empty_stacks(resp=None):
    assert _override_ctx_stack.top is None
    assert _additional_ctx_stack.top is None
    return resp


allows = Allows(
    app=app,
    identity_loader=lambda: g.user,
    on_fail=lambda *a, **k: ("nope", 403),
)


@app.before_request
def load_user():
    username = request.headers.get("Authorization")
    user = users.get(username, users["guest"])
    g.user = user


@app.before_request
def block_banned():
    allows.additional.current.add(Not(HasLevel(AuthLevels.banned)))


@app.before_request
def add_override():
    override = request.headers.get("Override")
    if override:
        allows.overrides.current.add(HasPermission(override))


class HasPermission(Requirement):

    def __init__(self, name):
        self.name = name

    def fulfill(self, user):
        return user.has_permission(self.name)

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return isinstance(other, HasPermission) and self.name == other.name

    def __repr__(self):
        return "HasPermission({})".format(self.name)


class HasLevel(Requirement):

    def __init__(self, userlevel):
        self.userlevel = userlevel

    def fulfill(self, user):
        return self.userlevel == user.userlevel

    def __hash__(self):
        return hash(self.userlevel)

    def __eq__(self, other):
        return isinstance(
            other, HasLevel
        ) and self.userlevel == other.userlevel

    def __repr__(self):
        return "HasLevel({})".format(self.userlevel)


@app.route("/")
# empty, run any ambient additional requirements
# should add this as a feature...?
@requires()
def index():
    return "Welcome", 200


@app.route("/promote")
@requires(HasPermission("promote"))
def promote():
    return "promoted", 200


class ItemsView(MethodView):
    decorators = [requires(HasPermission("view"))]

    def get(self):
        return "the things", 200

    @requires(HasPermission("reply"))
    def post(self):
        return "posted reply", 200

    @requires(HasPermission("edit"))
    def patch(self):
        return "updated", 200


app.add_url_rule("/items", view_func=ItemsView.as_view(name="items"))


@app.route("/raise")
def raiser():
    allows.overrides.current.add(lambda u: True)
    raise Exception()


@app.route("/use-permission")
def use_permission():
    with Permission(
        Or(
            HasLevel(AuthLevels.admin),
            HasLevel(AuthLevels.staff),
            And(HasLevel(AuthLevels.user), HasPermission("promote")),
        )
    ):
        pass
    return "thumbs up"


@app.route("/odd-perm")
@requires(C(HasLevel("admin"), HasPermission("ban"), op=operator.xor))
def odd_perm():
    return "thumbsup"


@app.route("/misbehave")
def misbehave():
    # push our own contexts and forget to remove them
    # after request handler will be made if the extension doesn't
    # clean them up
    allows.overrides.push(Override())
    allows.additional.push(Additional())


bp = Blueprint("test_integration_bp", "bp")
bp.before_request(guard_blueprint([HasPermission("promote")]))


@bp.route("/")
def bp_index():
    return "hello from permissioned endpoint"


@bp.route("/exempt")
@exempt_from_requirements
def exempt():
    return "hello from exempt endpoint"


failure = Blueprint("test_integration_failure", "failure")
failure.before_request(
    guard_blueprint(
        [HasPermission("promote")], on_fail=lambda **k: ("bp nope", 403)
    )
)


@failure.route("/")
def failure_index():
    return None


cbv = Blueprint("test_integration_cbv", "cbv")
cbv.before_request(guard_blueprint([HasPermission("promote")]))


class SomeCBV(MethodView):
    decorators = [exempt_from_requirements]

    def get(self):
        return "hello"


cbv.add_url_rule("/", view_func=SomeCBV.as_view(name="exempt"))


multi = Blueprint("test_integration_multi", "multi")
multi.before_request(
    guard_blueprint(
        [HasPermission("ban")],
        on_fail=lambda *a, **k: ("must be able to ban", 403),
    )
)
multi.before_request(
    guard_blueprint(
        [HasLevel(AuthLevels.staff)],
        on_fail=lambda *a, **k: ("must be staff", 403),
    )
)


@multi.route("/")
def multi_index():
    return "hello"


def view_args_to_resp(*a, **k):
    return jsonify(k)


has_view_args = Blueprint("test_integration_args", "args")
has_view_args.before_request(
    guard_blueprint([HasPermission("noone")], on_fail=view_args_to_resp)
)


@has_view_args.route("/<foo>/<bar>/")
def has_view_args_index():
    return ""


app.register_blueprint(bp, url_prefix="/bp")
app.register_blueprint(failure, url_prefix="/failure")
app.register_blueprint(cbv, url_prefix="/cbv")
app.register_blueprint(multi, url_prefix="/multi")
app.register_blueprint(has_view_args, url_prefix="/args")


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# THIS IS WHERE THE TESTS BEGIN


def test_blocks_guests_from_entering(client):
    rv = client.get("/", headers={"Authorization": "banned"})
    assert rv.data == b"nope"
    assert rv.status_code == 403


def test_must_have_view_to_access_items(client):
    rv = client.get("/items", headers={"Authorization": "banned"})
    assert rv.data == b"nope"
    assert rv.status_code == 403


@pytest.mark.parametrize("user", ["guest", "user", "admin", "staff"])
def test_can_view_items(user, client):
    rv = client.get("/items", headers={"Authorization": user})
    assert rv.data == b"the things"
    assert rv.status_code == 200


@pytest.mark.parametrize("user", ["banned", "guest"])
def test_must_have_reply_to_access_reply(user, client):
    rv = client.post("/items", headers={"Authorization": user})
    assert rv.data == b"nope"
    assert rv.status_code == 403


@pytest.mark.parametrize("user", ["user", "admin", "staff"])
def test_can_post_item_reply(user, client):
    rv = client.post("/items", headers={"Authorization": user})
    assert rv.data == b"posted reply"
    assert rv.status_code == 200


def test_can_post_reply_with_override(client):
    rv = client.post(
        "/items", headers={"Authorization": "guest", "Override": "reply"}
    )
    assert rv.data == b"posted reply"
    assert rv.status_code == 200


def test_recovers_from_endpoint_that_raises(client):
    rv = client.get("/raise")
    assert rv.status_code == 500


@pytest.mark.parametrize("user", ["admin", "staff"])
def test_can_access_permissioned_endpoint(user, client):
    rv = client.get("/use-permission", headers={"Authorization": user})
    assert rv.status_code == 200
    assert rv.data == b"thumbs up"


def test_can_access_permissioned_endpoint_with_override(client):
    rv = client.get(
        "/use-permission",
        headers={"Authorization": "user", "Override": "promote"},
    )
    assert rv.status_code == 200
    assert rv.data == b"thumbs up"


# python2 dict.keys returns a list, python3 doesn't have views
@pytest.mark.parametrize("user", set(users.keys()) - {"admin", "staff"})
def test_cant_access_permissioned_endpoint(user, client):
    rv = client.get("/use-permission", headers={"Authorization": user})
    assert rv.status_code == 403


def test_odd_permission(client):
    # has neither, xor should be false
    rv = client.get("/odd-perm", headers={"Authorization": "guest"})
    assert rv.status_code == 403

    # has both, xor should be false
    rv = client.get("/odd-perm", headers={"Authorization": "admin"})
    assert rv.status_code == 403

    # has one, xor should be true
    rv = client.get("/odd-perm", headers={"Authorization": "staff"})
    assert rv.status_code == 200

    # has one because of override, xor should be True
    rv = client.get(
        "/odd-perm", headers={"Authorization": "admin", "Override": "ban"}
    )
    assert rv.status_code == 200


def test_cleans_up_lingering_contexts(client):
    # endpoint pushes its own contexts but doesn't clean them up
    # asserts the extension object does clean them up
    client.get("/misbehave")
    assert not allows.additional.current
    assert not allows.overrides.current


def test_exempts_from_blueprint_requirements(client):
    rv = client.get("/bp/exempt", headers={"Authorization": "guest"})
    assert rv.status_code == 200


@pytest.mark.parametrize("user", ["guest", "user", "admin"])
def test_blocks_unpermissioned_from_accessing_blueprint(user, client):
    rv = client.get("/bp/", headers={"Authorization": user})
    assert rv.status_code == 403


def test_allows_user_to_access_blueprint(client):
    rv = client.get("/bp/", headers={"Authorization": "staff"})
    assert rv.status_code == 200
    assert b"permissioned" in rv.data


@pytest.mark.parametrize("user", ["guest", "user", "admin"])
def test_override_works_with_permission_blueprint(user, client):
    rv = client.get(
        "/bp/", headers={"Authorization": user, "Override": "promote"}
    )
    assert rv.status_code == 200
    assert b"permissioned" in rv.data


def test_blueprint_guard_can_return_early_response(client):
    rv = client.get("/failure/", headers={"Authorization": "user"})
    assert rv.status_code == 403
    assert b"bp nope" in rv.data


def test_exempts_cbv_when_class_decorated(client):
    rv = client.get("/cbv/", headers={"Authorization": "user"})
    assert rv.status_code == 200


def test_multi_tiered_guard_triggers_separately(client):
    rv = client.get("/multi/", headers={"Authorization": "user"})
    assert rv.status_code == 403
    assert b"ban" in rv.data

    rv = client.get("/multi/", headers={"Authorization": "admin"})
    assert rv.status_code == 403
    assert b"staff" in rv.data

    rv = client.get("/multi/", headers={"Authorization": "staff"})
    assert rv.status_code == 200
    assert b"hello" == rv.data


def test_guard_blueprint_passes_view_args_to_on_fail(client):
    rv = client.get("/args/foo/bar/")
    data = json.loads(rv.data.decode("utf-8"))
    assert data == {"foo": "foo", "bar": "bar"}
