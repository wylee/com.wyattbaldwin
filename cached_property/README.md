# Cached Property

Provides a thread safe `@cached_property` decorator that can be used
in place of the built in `@property` decorator for properties that are
expensive to compute or that aren't expected to change over the lifetime
of an instance.

## Usage

    >>> from cached_property import cached_property
    >>> class MyClass:
    ...     @cached_property
    ...     def prop(self):
    ...         return 2 ** 42
    ...
    >>> instance = MyClass()
    >>> "prop" in instance.__dict__
    False
    >>> instance.prop  # value computed and cached
    4398046511104
    >>> "prop" in instance.__dict__
    True
    >>> instance.prop  # cached value returned directly
    4398046511104
