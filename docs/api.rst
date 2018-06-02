.. _api:

################
flask_allows API
################

Extension
=========
.. autoclass:: flask_allows.allows.Allows
    :members:

Permission Helper
=================

.. autoclass:: flask_allows.permission.Permission
    :members:

Requirements Base Classes
=========================

.. autoclass:: flask_allows.requirements.Requirement
    :members:

.. autoclass:: flask_allows.requirements.ConditionalRequirement
    :members:


Override Management
===================

.. autoclass:: flask_allows.overrides.Override
    :members:

.. autoclass:: flask_allows.overrides.OverrideManager
    :members:


.. autoclass:: flask_allows.additional.Additional
    :members:

.. autoclass:: flask_allows.additional.AdditionalManager
    :members:


Utilities
=========

.. autofunction:: flask_allows.views.requires
.. autofunction:: flask_allows.views.exempt_from_requirements
.. autofunction:: flask_allows.views.guard_blueprint
.. autofunction:: flask_allows.requirements.wants_request
