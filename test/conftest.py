from collections import namedtuple

import pytest
from flask import Flask

from flask_allows import Requirement
from flask_allows.additional import _additional_ctx_stack
from flask_allows.overrides import _override_ctx_stack


class AuthLevels:
    banned = -2
    guest = -1
    member = 0
    moderator = 1
    admin = 2


class SpyRequirement(Requirement):
    def __init__(self):
        self.called = False
        self.called_with = {}

    def fulfill(self, user):
        self.called = True
        self.called_with["user"] = user


class AlwaysRequirement(SpyRequirement):
    def fulfill(self, user):
        super(AlwaysRequirement, self).fulfill(user)
        return True


class NeverRequirement(SpyRequirement):
    def fulfill(self, user):
        super(NeverRequirement, self).fulfill(user)
        return False


class CountingRequirement(AlwaysRequirement):
    def __init__(self):
        super(CountingRequirement, self).__init__()
        self.count = 0

    def fulfill(self, user):
        self.count += 1
        return super(CountingRequirement, self).fulfill(user)


user = namedtuple("User", ["name", "is_authed", "permlevel"])


@pytest.fixture(scope="session")
def authlevels():
    return AuthLevels


@pytest.fixture
def app():
    application = Flask(__name__)
    return application


@pytest.fixture
def spy():
    return SpyRequirement()


@pytest.fixture
def always():
    return AlwaysRequirement()


@pytest.fixture
def never():
    return NeverRequirement()


@pytest.fixture
def counter():
    return CountingRequirement()


@pytest.fixture(scope="session")
def member(authlevels):
    return user("member", True, authlevels.member)


@pytest.fixture(scope="session")
def admin(authlevels):
    return user("admin", True, authlevels.admin)


@pytest.fixture(scope="session")
def guest(authlevels):
    return user("guest", False, authlevels.guest)


@pytest.fixture(scope="session")
def banned(authlevels):
    return user("banned", False, authlevels.banned)


@pytest.fixture(scope="session")
def moderator(authlevels):
    return user("mod", True, authlevels.moderator)


@pytest.fixture(scope="session")
def atleastmod(authlevels):
    return lambda u, r: u.permlevel >= authlevels.moderator


@pytest.fixture(scope="session")
def adminrequired(authlevels):
    return lambda u, r: u.permlevel == authlevels.admin


@pytest.fixture(scope="session")
def isauthed(authlevels):
    return lambda u, r: u.is_authed


@pytest.fixture(scope="session")
def ismember(authlevels):
    return lambda u, r: u.permlevel >= authlevels.member


@pytest.fixture(scope="session")
def readonly():
    return lambda u, r: r.method.upper() == "GET"


# both this and the cleanup method will cause a test suite to fail horribly
# if either fail so it's no more dangerous to handle both contexts in each
# callable than in separate ones
@pytest.fixture(autouse=True)
def ensure_context_is_empty():
    assert _override_ctx_stack.top is None
    assert _additional_ctx_stack.top is None
    yield


@pytest.fixture(autouse=True)
def pop_til_you_stop():
    yield
    while _override_ctx_stack.top is not None:
        _override_ctx_stack.pop()

    while _additional_ctx_stack.top is not None:
        _additional_ctx_stack.pop()
