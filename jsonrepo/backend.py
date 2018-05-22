# -*- coding: utf8 -*-
"""
Storage backend definition
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""


class Backend(object):
    """ Basic backend class """
    def __init__(self, prefix, secondary_indexes):
        self._prefix = prefix
        self._secondary_indexes = secondary_indexes

    def prefixed(self, key):
        """ build a prefixed key """
        return '{}:{}'.format(self._prefix, key)

    def get(self, key, sort_key):
        raise NotImplementedError

    def set(self, key, sort_key, value):
        raise NotImplementedError

    def delete(self, key, sort_key):
        raise NotImplementedError

    def history(self, key, _from='-', _to='+', _desc=True):
        raise NotImplementedError

    def find(self, index, value):
        raise NotImplementedError
