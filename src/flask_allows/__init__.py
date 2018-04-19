from .allows import Allows, allows  # noqa
from .overrides import Override, OverrideManager, overrides  # noqa
from .permission import Permission  # noqa
from .requirements import (And, C, ConditionalRequirement, Not, Or,
                           Requirement, wants_request)  # noqa
from .views import PermissionedMethodView, PermissionedView, requires  # noqa

__all__ = (
    'allows',
    'Allows',
    'And',
    'C',
    'ConditionalRequirement',
    'Not',
    'Or',
    'Override',
    'OverrideManager',
    'overrides'
    'Permission',
    'PermissionedMethodView',
    'PermissionedView'
    'Requirement',
    'requires',
    'wants_request',
)

__version__ = "0.5.1"
__author__ = 'Alec Nikolas Reiter'
