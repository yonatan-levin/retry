import time

class SimpleCache:
    def __init__(self, expiration=300):
        self.expiration = expiration
        self.store = {}

    def contains(self, key):
        return key in self.store and (time.time() - self.store[key]['time']) < self.expiration

    def get(self, key):
        return self.store[key]['value']

    def set(self, key, value):
        self.store[key] = {'value': value, 'time': time.time()}
