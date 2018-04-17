from .allows import Allows, allows  # noqa
from .permission import Permission  # noqa
from .requirements import Or  # noqa
from .requirements import And, C, ConditionalRequirement, Not, Requirement
from .views import PermissionedMethodView, PermissionedView, requires  # noqa

__all__ = (
    'allows',
    'Allows',
    'And',
    'C',
    'ConditionalRequirement',
    'Not',
    'Or',
    'Permission',
    'PermissionedMethodView',
    'PermissionedView'
    'Requirement',
    'requires',
)

__version__ = "0.5.0"
__author__ = 'Alec Nikolas Reiter'
