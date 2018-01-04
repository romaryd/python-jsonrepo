# -*- coding: utf8 -*-
"""
Storage Mixin
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
from awesomedecorators import memoized
from jsonrepo.backends.redis import RedisBackend
from jsonrepo.backends.memory import DictBackend
from jsonrepo.backends.dynamodb import DynamoDBBackend


class StorageMixin(object):
    """
    Mix in storage capacity with singleton
    """
    @memoized
    def storage(self):
        """
        Instantiates and returns a storage instance
        """
        if self.backend == 'redis':
            return RedisBackend(self.prefix)
        if self.backend == 'dynamodb':
            return DynamoDBBackend(self.prefix, self.key, self.sort_key)
        return DictBackend(self.prefix)
