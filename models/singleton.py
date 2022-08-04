"""
This Singleton class is used to ensure we only instantiate one instance of the database connection object.
"""
class Singleton:

    def __init__(self, cls):
        self._cls = cls

    def instance(self):

        try:
            return self._instance
        except AttributeError:
            self._instance = self._cls()
            return self._instance

    def __call__(self):
        raise TypeError('Singletons must be accessed through `.instance()`')

    def __instancecheck__(self, instance):
        return isinstance(inst, self._cls)