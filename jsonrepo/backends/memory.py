# -*- coding: utf8 -*-
"""
In process memory implementation of storage backend
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
from loggingmixin import LoggingMixin
from awesomedecorators import memoized
from jsonrepo.backend import Backend

CACHE = {}


class DictBackend(Backend, LoggingMixin):
    """
    Backend based on in process memory
    """
    @memoized
    def cache(self):
        """ In memory storage as a dictionary """
        return CACHE

    def get(self, key, sort_key):
        """ Get an element in dictionary """
        key = self.prefixed('{}:{}'.format(key, sort_key))
        self.logger.debug('Storage - get {}'.format(key))
        if key not in self.cache.keys():
            return None
        return self.cache[key]

    def set(self, key, sort_key, value):
        primary_key = key
        key = self.prefixed('{}:{}'.format(key, sort_key))
        """ Set an element in dictionary """
        self.logger.debug('Storage - set value {} for {}'.format(value, key))
        if (self.prefixed(primary_key) not in self.cache.keys() and
           sort_key is not None):
            self.cache[self.prefixed(primary_key)] = []
        if sort_key is not None:
            self.cache[self.prefixed(primary_key)].append(sort_key)
            self.cache[self.prefixed(primary_key)] = sorted(
                self.cache[self.prefixed(primary_key)])
        self.cache[key] = value
        return self.cache[key] is value

    def delete(self, key, sort_key):
        primary_key = key
        key = self.prefixed('{}:{}'.format(key, sort_key))
        """ Delete an element in dictionary """
        self.logger.debug('Storage - delete {}'.format(key))
        if sort_key is not None:
            self.cache[self.prefixed(primary_key)].remove(sort_key)
        del(self.cache[key])

    def history(self, key, _from='-', _to='+', _desc=True):
        if _from == '-':
            _from = ''
        res = []
        if self.prefixed(key) in self.cache:
            for k in self.cache[self.prefixed(key)]:
                if k > _from:
                    if _to != '+':
                        if k > _to:
                            break
                    res.append(k)
            if _desc:
                return [self.get(key, kid) for kid in res][::-1]
        return [self.get(key, kid) for kid in res]

    def latest(self, key):
        self.logger.debug('Storage - get latest for {}'.format(
            self.prefixed(key)
        ))
        if self.prefixed(key) not in self.cache:
            return None
        if len(self.cache[self.prefixed(key)]) == 0:
            return None
        return self.get(key, self.cache[self.prefixed(key)][-1])
