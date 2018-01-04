# -*- coding: utf8 -*-
# Storage Mixin
#
# Author:   Romary Dupuis <romary@me.com>
#
# Copyright (C) 2017 Romary Dupuis

import os
import redis
import boto3
import json
from six import add_metaclass
from boto3.dynamodb.conditions import Key
from awesomedecorators import memoized
from singleton import Singleton
from loggingmixin import LoggingMixin
from collections import OrderedDict

__version__ = '0.1.0'

CACHE = {}


def namedtuple_asdict(obj):
    """
    Serializing a nested namedtuple into a Python dict
    """
    if obj is None:
        return obj
    if hasattr(obj, "_asdict"):  # detect namedtuple
        return OrderedDict(zip(obj._fields, (namedtuple_asdict(item)
                                             for item in obj)))
    if isinstance(obj, str):  # iterables - strings
        return obj
    if hasattr(obj, "keys"):  # iterables - mapping
        return OrderedDict(zip(obj.keys(), (namedtuple_asdict(item)
                                            for item in obj.values())))
    if hasattr(obj, "__iter__"):  # iterables - sequence
        return type(obj)((namedtuple_asdict(item) for item in obj))
    # non-iterable cannot contain namedtuples
    return obj


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


@add_metaclass(Singleton)
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


@add_metaclass(Singleton)
class DynamoDBBackend(Backend, LoggingMixin):
    """
    Backend based on DynamoDB
    """
    def __init__(self, prefix, key, sort_key):
        self._prefix = prefix
        self._key = key
        self._sort_key = sort_key

    @memoized
    def dynamodb_server(self):
        dynamodb = boto3.resource('dynamodb')
        return dynamodb.Table(self._prefix)

    def get(self, key, sort_key):
        self.logger.debug('Storage - get {}'.format(self.prefixed(key)))
        res = self.dynamodb_server.get_item(Key={
            self._key: self.prefixed(key),
        })
        if 'Item' in res and 'value' in res['Item']:
            return res['Item']['value']

    def set(self, key, sort_key, value):
        self.logger.debug('Storage - set value {} for {}'
                          .format(value,
                                  self.prefixed(key)))
        item = {
            self._key: self.prefixed(key),
            'value': value
        }
        if sort_key is not None:
            item.update({
                self._sort_key: sort_key
            })
        return self.dynamodb_server.put_item(Item=item)

    def delete(self, key, sort_key):
        self.logger.debug('Storage - delete {}'.format(self.prefixed(key)))
        return self.dynamodb_server.delete_item(Key={
            self._key: self.prefixed(key)
        })

    def history(self, key, _from='-', _to='+', _desc=True):
        if _from != '-':
            response = self.dynamodb_server.query(
                KeyConditionExpression=Key(self._key)
                .eq(self.prefixed(key)) &
                Key(self._sort_key)
                .gt(_from),
                Limit=100
            )
            return [item['value'] for item in response['Items']]
        if _to != '+':
            response = self.dynamodb_server.query(
                KeyConditionExpression=Key(self._key)
                .eq(self.prefixed(key)) &
                Key(self._sort_key)
                .lt(_to),
                Limit=100,
                ScanIndexForward=False
            )
            return [item['value'] for item in response['Items']]
        return []

    def latest(self, key):
        response = self.dynamodb_server.query(
            KeyConditionExpression=Key(self._key)
            .eq(self.prefixed(key)),
            Limit=1,
            ScanIndexForward=False
        )
        if len(response['Items']) > 0:
            return response['Items'][0]['value']
        else:
            return None


@add_metaclass(Singleton)
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
        if self.prefixed(key) not in self.cache:
            return None
        if len(self.cache[self.prefixed(key)]) == 0:
            return None
        return self.get(key, self.cache[self.prefixed(key)][-1])


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


class Record(object):
    """
    Definition of a JSON serializable record for a repository
    """
    def from_json(cls, json_dump):
        """
        JSON deserialization
        """
        raise NotImplementedError

    def to_json(self):
        """
        JSON serialization
        """
        raise NotImplementedError


class DictRecord(Record):
    """
    Specific implementation of a record based on a dictionary
    """
    @classmethod
    def from_json(cls, json_dump):
        """
        How to get a context from a json dump
        """
        context = cls()
        ctxt = json.loads(json_dump)
        for k in ctxt:
            context[k] = ctxt[k]
        return context

    def to_json(self):
        """
        JSON serialization
        """
        return json.dumps(self.copy())


class NamedtupleRecord(Record):
    """
    Specific implementation of a record based on a namedtuple
    """
    @classmethod
    def from_json(cls, json_dump):
        kwargs = json.loads(json_dump)
        return cls(**kwargs)

    def to_json(self):
        return json.dumps(namedtuple_asdict(self))


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
