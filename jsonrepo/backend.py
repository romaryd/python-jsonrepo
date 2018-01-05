# -*- coding: utf8 -*-
"""
Storage backend definition
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""


class Backend(object):
    """ Basic backend class """
    def __init__(self, prefix):
        self._prefix = prefix

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
