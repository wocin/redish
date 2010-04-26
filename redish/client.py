from redis import Redis as _RedisClient

from redish import types
from redish.utils import key
from redish.serialization import Pickler

DEFAULT_PORT = 6379


class Client(object):
    host = "localhost"
    port = DEFAULT_PORT
    db = None
    serializer = Pickler()
    #serializer = anyjson

    def __init__(self, host=None, port=None, db=None,
            serializer=None):
        self.host = host or self.host
        self.port = port or self.port
        self.serializer = serializer or self.serializer
        self.db = db or self.db
        self.api = _RedisClient(self.host, self.port, self.db)

    def id(self, name):
        return types.Id(name, self.api)

    def List(self, name, initial=None):
        """The list datatype.

        :param name: The name of the list.
        :keyword initial: Initial contents of the list.

        """
        return types.List(name, self.api, initial=initial)

    def SortedSet(self, name):
        """The sorted set datatype.

        :param name: The name of the sorted set.

        """
        return types.SortedSet(name, self.api)

    def Set(self, name):
        """The set datatype.

        :param name: The name of the set.

        """
        return types.Set(name, self.api)

    def Dict(self, name, initial=None, **extra):
        """The dictionary datatype (Hash).

        :param name: The name of the dictionary.
        :keyword initial: Initial contents.
        :keyword \*\*extra: Initial contents as keyword arguments.

        The ``initial``, and ``**extra`` keyword arguments
        will be merged (keyword arguments has priority).

        """
        return types.Dict(name, self.api, initial=initial, **extra)

    def Counter(self, name, initial=None):
        """The counter datatype.

        :param name: Name of the counter.
        :keyword initial: Initial value of the counter.

        """
        return types.Counter(name, self.api, initial=initial)

    def Queue(self, name, initial=None):
        """The queue datatype.

        :param name: The name of the queue.
        :keyword initial: Initial items in the queue.

        """
        return types.Queue(name, self.api, initial=initial)

    def LIFOQueue(self, name, initial=None):
        """The LIFO queue datatype.

        :param name: The name of the queue.
        :keyword initial: Initial items in the queue.

        """
        return types.LIFOQueue(name, self.api, initial=initial)

    def prepare_value(self, value):
        """Encode python object to be stored in the database."""
        return self.serializer.serialize(value)

    def value_to_python(self, value):
        """Decode value to a Python object."""
        return self.serializer.deserialize(value)

    def clear(self):
        """Remove all keys from the current database."""
        return self.api.flushdb()

    def update(self, mapping):
        """Update database with the key/values from a :class:`dict`."""
        return self.api.mset(mapping)

    def rename(self, old_name, new_name):
        """Rename key to a new name."""
        return self.api.rename(key(old_name), key(new_name))

    def keys(self, pattern="*"):
        """Get a list of all the keys in the database, or
        matching ``pattern``."""
        return self.api.keys(pattern)

    def iterkeys(self, pattern="*"):
        """An iterator over all the keys in the database, or matching
        ``pattern``."""
        return iter(self.keys(pattern))

    def iteritems(self, pattern="*"):
        """An iterator over all the ``(key, value)`` items in the database,
        or where the keys matches ``pattern``."""
        for key in self.keys(pattern):
            yield (key, self[key])

    def items(self, pattern="*"):
        """Get a list of all the ``(key, value)`` pairs in the database,
        or the keys matching ``pattern``, as 2-tuples."""
        return list(self.iteritems(pattern))

    def itervalues(self, pattern="*"):
        """Iterate over all the values in the database, or those where the
        keys matches ``pattern``."""
        for key, value in self.iteritems(pattern):
            yield value

    def values(self, pattern="*"):
        """Get a list of all values in the database, or those where the
        keys matches ``pattern``."""
        return list(self.itervalues(pattern))

    def pop(self, name):
        """Get and remove key from database (atomic)."""
        name = key(name)
        temp = key((name, "__poptmp__"))
        if self.rename(name, temp):
            value = self[temp]
            del(self[temp])
            return value
        raise KeyError(name)

    def __getitem__(self, name):
        """``x.__getitem__(name) <==> x[name]``"""
        name = key(name)
        value = self.api.get(name)
        if value is None:
            raise KeyError(name)
        return self.value_to_python(value)

    def get(self, key, default=None):
        """Returns the value at ``key`` if present, otherwise returns
        ``default`` (``None`` by default.)"""
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, name, value):
        """``x.__setitem(name, value) <==> x[name] = value``"""
        return self.api.set(key(name), self.prepare_value(value))

    def __delitem__(self, name):
        """``x.__delitem__(name) <==> del(x[name])``"""
        name = key(name)
        if not self.api.delete(name):
            raise KeyError(name)

    def __len__(self):
        """``x.__len__() <==> len(x)``"""
        return self.api.dbsize()

    def __contains__(self, name):
        """``x.__contains__(name) <==> name in x``"""
        return self.api.exists(key(name))

    def __repr__(self):
        """``x.__repr__() <==> repr(x)``"""
        return "<RedisClient: %s:%s/%s>" % (self.host,
                                           self.port,
                                           self.db or "")
