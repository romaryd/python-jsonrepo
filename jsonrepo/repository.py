# -*- coding: utf8 -*-
"""
Storage Mixin and repository for JSON serializable objects
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
from six import add_metaclass
from singleton import Singleton
from loggingmixin import LoggingMixin
from jsonrepo.mixin import StorageMixin
from jsonrepo.record import Record


@add_metaclass(Singleton)
class Repository(StorageMixin, LoggingMixin):
    """
    Definition of a repository
    """
    backend = 'dict'
    prefix = ''
    klass = Record
    key = ''
    sort_key = ''
    secondary_indexes = []

    def storage_get(self, key, sort_key):
        return self.storage.get(key, sort_key)

    def get(self, key, sort_key, klass=None, **args):
        """
        Retrieves a context object
        """
        if klass is None:
            klass = self.klass
        record = self.storage_get(key, sort_key)
        if record is None:
            return klass(**args)
        return klass.from_json(record)

    def save(self, key, sort_key, _object):
        """
        Saves a context object
        """
        return self.storage.set(key, sort_key, _object.to_json())

    def delete(self, key, sort_key):
        """
        Saves a context object
        """
        return self.storage.delete(key, sort_key)

    def history(self, key, _from='-', _to='+', _desc=True):
        """
        Retrives a list of records according to a datetime range
        """
        return [self.klass.from_json(_object)
                for _object in self.storage.history(key, _from, _to, _desc)]

    def latest(self, key):
        """
        Get the most recent record for a specific key
        """
        return self.klass.from_json(self.storage.latest(key))

    def find(self, index, value):
        """
        Find record according to the value of a secondary index
        """
        res = self.storage.find(index, value)
        return {
            'count': res['count'],
            'items': [self.klass.from_json(_object)
                      for _object in res['items']]
        }
