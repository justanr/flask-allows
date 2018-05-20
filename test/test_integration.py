import operator

import pytest
from flask import Flask, g, request
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
    requires,
)
from flask_allows.additional import _additional_ctx_stack
from flask_allows.overrides import _override_ctx_stack

integration = pytest.mark.integration

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


@pytest.fixture
def client():
    with app.test_client() as client:
        yield client


# THIS IS WHERE THE TESTS BEGIN


@integration
def test_blocks_guests_from_entering(client):
    rv = client.get("/", headers={"Authorization": "banned"})
    assert rv.data == b"nope"
    assert rv.status_code == 403


@integration
def test_must_have_view_to_access_items(client):
    rv = client.get("/items", headers={"Authorization": "banned"})
    assert rv.data == b"nope"
    assert rv.status_code == 403


@integration
@pytest.mark.parametrize("user", ["guest", "user", "admin", "staff"])
def test_can_view_items(user, client):
    rv = client.get("/items", headers={"Authorization": user})
    assert rv.data == b"the things"
    assert rv.status_code == 200


@integration
@pytest.mark.parametrize("user", ["banned", "guest"])
def test_must_have_reply_to_access_reply(user, client):
    rv = client.post("/items", headers={"Authorization": user})
    assert rv.data == b"nope"
    assert rv.status_code == 403


@integration
@pytest.mark.parametrize("user", ["user", "admin", "staff"])
def test_can_post_item_reply(user, client):
    rv = client.post("/items", headers={"Authorization": user})
    assert rv.data == b"posted reply"
    assert rv.status_code == 200


@integration
def test_can_post_reply_with_override(client):
    rv = client.post(
        "/items", headers={"Authorization": "guest", "Override": "reply"}
    )
    assert rv.data == b"posted reply"
    assert rv.status_code == 200


@integration
def test_recovers_from_endpoint_that_raises(client):
    rv = client.get("/raise")
    assert rv.status_code == 500


@integration
@pytest.mark.parametrize("user", ["admin", "staff"])
def test_can_access_permissioned_endpoint(user, client):
    rv = client.get("/use-permission", headers={"Authorization": user})
    assert rv.status_code == 200
    assert rv.data == b"thumbs up"


@integration
def test_can_access_permissioned_endpoint_with_override(client):
    rv = client.get(
        "/use-permission",
        headers={"Authorization": "user", "Override": "promote"},
    )
    assert rv.status_code == 200
    assert rv.data == b"thumbs up"


@integration
# python2 dict.keys returns a list, python3 doesn't have views
@pytest.mark.parametrize("user", set(users.keys()) - {"admin", "staff"})
def test_cant_access_permissioned_endpoint(user, client):
    rv = client.get("/use-permission", headers={"Authorization": user})
    assert rv.status_code == 403


@integration
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


@integration
def test_cleans_up_lingering_contexts(client):
    # endpoint pushes its own contexts but doesn't clean them up
    # asserts the extension object does clean them up
    client.get("/misbehave")
    assert not allows.additional.current
    assert not allows.overrides.current
