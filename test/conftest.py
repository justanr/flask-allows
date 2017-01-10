from flask import request as flask_request, Flask
from flask_allows import Requirement
from collections import namedtuple
import pytest


class SpyRequirement(Requirement):
    def __init__(self):
        self.called = False
        self.called_with = {}

    def fulfill(self, user, request):
        self.called = True
        self.called_with['user'] = user
        self.called_with['request'] = request


class AlwaysRequirement(SpyRequirement):
    def fulfill(self, user, request):
        super(AlwaysRequirement, self).fulfill(user, request)
        return True


class NeverRequirement(SpyRequirement):
    def fulfill(self, user, request):
        super(NeverRequirement, self).fulfill(user, request)
        return False


user = namedtuple('User', ['name', 'is_authed', 'permlevel'])


@pytest.fixture(scope='session')
def request():
    return flask_request


@pytest.fixture(scope='session')
def authlevels():
    class AuthLevels:
        banned = -2
        guest = -1
        member = 0
        moderator = 1
        admin = 2

    return AuthLevels


@pytest.fixture
def func_requirement():
    def authorizer(user, request):
        authorizer.called = True
        return True
    authorizer.called = False
    return authorizer


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


@pytest.fixture(scope='session')
def member(authlevels):
    return user('member', True, authlevels.member)


@pytest.fixture(scope='session')
def admin(authlevels):
    return user('admin', True, authlevels.admin)


@pytest.fixture(scope='session')
def guest(authlevels):
    return user('guest', False, authlevels.guest)


@pytest.fixture(scope='session')
def banned(authlevels):
    return user('banned', False, authlevels.banned)


@pytest.fixture(scope='session')
def moderator(authlevels):
    return user('mod', True, authlevels.moderator)


@pytest.fixture(scope='session')
def atleastmod(authlevels):
    return lambda u, r: u.permlevel >= authlevels.moderator


@pytest.fixture(scope='session')
def adminrequired(authlevels):
    return lambda u, r: u.permlevel == authlevels.admin


@pytest.fixture(scope='session')
def isauthed(authlevels):
    return lambda u, r: u.is_authed


@pytest.fixture(scope='session')
def ismember(authlevels):
    return lambda u, r: u.permlevel >= authlevels.member


@pytest.fixture(scope='session')
def readonly():
    return lambda u, r: r.method.upper() == 'GET'
