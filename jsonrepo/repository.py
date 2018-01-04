# -*- coding: utf8 -*-
"""
Storage Mixin and repository for JSON serializable objects
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
from loggingmixin import LoggingMixin
from jsonrepo.mixin import StorageMixin
from jsonrepo.record import Record


class Repository(StorageMixin, LoggingMixin):
    """
    Definition of a repository
    """
    backend = 'dict'
    prefix = ''
    klass = Record
    key = ''
    sort_key = ''

    def storage_get(self, key, sort_key):
        return self.storage.get(key, sort_key)

    def get(self, key, sort_key, klass=None):
        """
        Retrieves a context object
        """
        if klass is None:
            klass = self.klass
        record = self.storage_get(key, sort_key)
        if record is None:
            return klass()
        return klass.from_json(record)

    def save(self, key, sort_key, _object):
        """
        Saves a context object
        """
        return self.storage.set(key, sort_key, _object.to_json())

    def history(self, key, _from='-', _to='+', _desc=True):
        """
        Saves a context object
        """
        return [self.klass.from_json(_object)
                for _object in self.storage.history(key, _from, _to, _desc)]

    def latest(self, key):
        """
        Saves a context object
        """
        return self.klass.from_json(self.storage.latest(key))
