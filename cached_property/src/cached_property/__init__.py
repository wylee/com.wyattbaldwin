import functools
import threading


__version__ = "1.1.dev0"


class cached_property:

    """Decorator that caches the computed value on first access.

    This is a replacement for the built-in ``@property`` decorator. It
    caches the computed value when the property is first accessed. This
    is useful when a property is expensive to compute.

    If the value needs to be recomputed, the attribute can be deleted
    from the instance as shown below.

    >>> value = object()
    >>>
    >>> class C:
    ...    @cached_property
    ...    def x(self):
    ...        return value
    ...
    >>> isinstance(C.x, cached_property)
    True
    >>> c = C()
    >>> 'x' in c.__dict__
    False
    >>> c.x is value
    True
    >>> 'x' in c.__dict__
    True
    >>> del c.x
    >>> 'x' in c.__dict__
    False

    """

    def __init__(self, function):
        self.function = function
        self.lock = threading.RLock()
        # Set __name__, __doc__, etc from the wrapped function on this
        # cached property so it looks like the wrapped function.
        functools.update_wrapper(self, function)

    def __get__(self, instance, cls=None):
        if instance is None:
            # When the property is accessed as a class attribute, return
            # the property itself.
            return self
        name = self.__name__
        instance_dict = instance.__dict__
        if name not in instance_dict:
            with self.lock:
                # Skip value computation if another thread computed and
                # cached the value while the current thread was waiting.
                if name not in instance_dict:
                    instance_dict[name] = self.function(instance)
        return getattr(instance, name)
