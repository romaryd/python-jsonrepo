# -*- coding: utf8 -*-
"""
Redis implementation of storage backend
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
import os
import redis
from loggingmixin import LoggingMixin
from awesomedecorators import memoized
from jsonrepo.backend import Backend


class RedisBackend(Backend, LoggingMixin):
    """
    Backend based on Redis
    """
    @memoized
    def redis_server(self):
        return redis.StrictRedis(host=os.environ.get('REDIS_HOST', '127.0.0.1'),
                                 port=os.environ.get('REDIS_PORT', 6379),
                                 db=os.environ.get('REDIS_DB', 0))

    def exists(self, key):
        return self.redis_server.exists(self.prefixed(key))

    def keys(self, pattern):
        return self.redis_server.keys(pattern)

    def get(self, key, sort_key):
        self.logger.debug('Storage - get {}'.format(
            self.prefixed('{}:{}'.format(key, sort_key))
        ))
        value = self.redis_server.get(
            self.prefixed('{}:{}'.format(key, sort_key))
        )
        if value is not None:
            return value.decode('utf-8')
        return value

    def set(self, key, sort_key, value):
        self.logger.debug('Storage - set value {} for {}'
                          .format(value,
                                  self.prefixed(
                                      '{}:{}'.format(key, sort_key)
                                  )))
        if sort_key is not None:
            self.redis_server.zadd(self.prefixed(key), 0.0, sort_key)
        return self.redis_server.set(self.prefixed(
            '{}:{}'.format(key, sort_key)), value)

    def delete(self, key, sort_key):
        self.logger.debug('Storage - delete {}'.format(self.prefixed(
            '{}:{}'.format(key, sort_key))))
        if sort_key is not None:
            self.redis_server.zrem(self.prefixed(key), sort_key)
        return self.redis_server.delete(self.prefixed(
            '{}:{}'.format(key, sort_key)))

    def history(self, key, _from='-', _to='+', _desc=True):
        if _from != '-':
            _from = '({}'.format(_from)
        if _to != '+':
            _to = '({}'.format(_to)
        res = [self.get(key, kid.decode('utf8'))
               for kid in self.redis_server.zrevrangebylex(
                   self.prefixed(key),
                   _to, _from,
                   start=0, num=100)]
        if not _desc:
            return res[::-1]
        return res

    def latest(self, key):
        self.logger.debug('Storage - get latest for {}'.format(
            self.prefixed(key)
        ))
        res = self.redis_server.zrevrangebylex(
            self.prefixed(key),
            '+', '-',
            start=0, num=1
        )
        if len(res) > 0:
            return self.get(key, res[0].decode('utf8'))
        else:
            return None

    def transaction(self, func, *watchs, **params):
        return self.redis_server.transaction(func, *watchs, **params)
