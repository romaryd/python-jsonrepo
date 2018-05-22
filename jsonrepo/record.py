# -*- coding: utf8 -*-
"""
Definition of JSON serializable record
Author:   Romary Dupuis <romary@me.com>
Copyright (C) 2017 Romary Dupuis
"""
from collections import OrderedDict
import json


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


class Record(object):
    """
    Definition of a JSON serializable record for a repository
    """
    @classmethod
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
        if json_dump is None:
            return None
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
        if json_dump is None:
            return None
        kwargs = json.loads(json_dump)
        return cls(**kwargs)

    def to_json(self):
        return json.dumps(namedtuple_asdict(self))
