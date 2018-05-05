.. _overrides:


########################################
Manipulating Requirements after the fact
########################################

Since requirements applied to route handlers are static, they can be quite
difficult to manipulate after the fact. Fancy foot work with requirement
factories can ease this some but at the cost of complexity, manual management
and potentially tricky application or request scoped context locals.

To address this, ``flask-allows`` provides a mechanism for overriding requirements
itself.


.. note::

    In order to use this feature with :ref:`Class Based Requirements`, you
    must define both an ``__eq__`` and ``__hash__`` method on the requirement::


        class Has(Requirement):
            def __init__(self, permission):
                self.permission = permission

            def fulfill(self, user):
                return self.permission in user.permissions

            def __eq__(self, other):
                return isinstance(other, Has) and self.permission == other.permission

            def __hash__(self):
                return hash(self.permission)

    Since this quite a bit of boilerplate, consider using
    `attrs <https://www.attrs.org>`_ in conjunction with this library as well::

        import attr


        @attr.s(frozen=True)
        class Has(Requirement):
            permission = attr.ib()

            def fulfill(self, user):
                return

    The downside here is that ``Has`` also becomes orderable, but see
    `python-attrs/attrs #170 <https://github.com/python-attrs/attrs/issues/170>`_
    for more details.


**********************
Disabling Requirements
**********************

Disabling requirements can be useful to temporarily allows a specific user
access to certain areas of your application. ``flask-allows`` exposes an
``overrides`` attribute on the extension object, as well as providing a
``current_overrides`` context local and an
:class:`~flask_allows.overrides.Override` class, each of these play a separate
role in the process:

- ``allows.overrides`` is the :class:`~flask_allows.overrides.OverrideManager`
  instance associated with the extension object. It is strongly recommended
  to use this instance rather than instantiating your own.

- ``current_overrides`` is a context local that points towards the current
  override context.

- :class:`~flask_allows.overrides.Override` is the representation of the
  override context.


.. note::

    ``current_overrides`` is a context local managed separately from the
    application and requests contexts. However, the Allows extension object
    registers before and after request handlers to push and cleanup override
    contexts.


``flask-allows`` automatically starts an override context at the beginning of
a request so  we can immediately being overriding requirements by calling
:meth:`~flask_allows.overrides.Override.add`::

    from flask_allows import current_overrides
    from .app.requirements import is_admin

    current_overrides.add(is_admin)


We can also remove a requirement from the override context with
:meth:`~flask_allows.overrides.Override.remove`::

    current_overrides.remove(is_admin)

Both ``add`` and ``remove`` accept multiple requirements but must always be passed
at least one requirement.

.. note::

    Adding and removing from ``current_overrides`` affects the current context
    directly. If this is an object you're holding a reference to, you will see
    the changes reflected in it.


It is possible to temporarily replace the current context with a new one with
``OverrideManager``'s :meth:`~flask_allows.overrides.OverrideManager.override`
method which acts as a context manager::

    with allows.overrides.override(Override(is_admin)):
        ...

When the block is entered, a new override context is pushed and when the block
exits, it is popped. This context manager also yields the new context into the
block for convenience sake::

    with allows.overrides.override(Override(is_admin)) as overrides:
        ...

If the new context should augment rather than entirely replace the current
context, you may supply the ``use_parent`` argument to ``override``::

    with allows.overrides.override(Override(is_admin), use_parent=True):
        ...

Behind the scenes, this creates a new Override instance that combines the
disabled requirements from the current context and the child context rather
than changing either's state directly. This makes transitioning back to the
original context easier.


If we need to check if the current override context overrides a requirement,
that is possible with either the ``is_overridden`` method or the ``in`` operator::

    current_overrides.is_overridden(is_admin)
    is_admin in current_overrides


***********************************
Manually managing override contexts
***********************************


We can also manually manage overrides on a global scale by using the manager's
:meth:`~flask_allows.overrides.OverrideManager.push` and
:meth:`~flask_allows.overrides.OverrideManager.pop` methods. This can be useful
when working outside the request-response cycle, such as in a CLI context or
out-of-band task runner such as celery.

.. danger::

    :meth:`~flask_allows.overrides.OverrideManager.pop` checks that the popped
    context belongs to the manager instance that popped the context. If a
    separate manager instance pushed the last context or if a context was not
    active when ``pop`` was called, a ``RuntimeError`` is raised to signal this
    error.


To begin a manual override context we must first call ``push`` method with an
``Override`` instance::

    allows.overrides.push(Override())

This replaces the current context rather than augments it and
``current_overrides`` points at this instance. If newly pushed context should
augment the existing context rather than replacing it entirely, you may supply
the ``use_parent`` argument -- this behaves the same as when provided with
the manager's ``override`` method.

When we are done with this context, we must call the ``pop`` method to end
the context and replace it with its parent::

    allows.overrides.pop()
