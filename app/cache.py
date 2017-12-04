class Cache(object):
    _cache = {}

    @classmethod
    def get(cls, key, default=None):
        try:
            return cls._cache[key]
        except KeyError:
            return default

    @classmethod
    def set(cls, key, value):
        cls._cache[key] = value
        return cls.get(key)

    @classmethod
    def purge(cls):
        """Remove all items from the cache"""
        cls._cache_ = {}
