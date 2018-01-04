# jsonrepo

[![Build Status](https://travis-ci.org/romaryd/python-jsonrepo.svg?branch=master)](https://travis-ci.org/romaryd/python-jsonrepo)
[![Coverage Status](https://coveralls.io/repos/github/romaryd/python-jsonrepo/badge.svg?branch=master)](https://coveralls.io/github/romaryd/python-jsonrepo?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/5d394fb9d6a3d88500ba/maintainability)](https://codeclimate.com/github/romaryd/python-jsonrepo/maintainability)
[![Code Health](https://landscape.io/github/romaryd/python-jsonrepo/master/landscape.svg?style=flat)](https://landscape.io/github/romaryd/python-jsonrepo/master)

---
Jsonrepo proposes a simple repository system for json serializable objects. It can run on
various storage backends such as Redis and DynamoDB.

A record in the repository is uniquely identified by a key and optionally a sort key.

Jsonrepo was initially thought with the purpose of using a date as sort key so that we can build, for example, a repository of messages for users. A record will be then identified by the user id and a datetime. The future will tell us if there is a need to be really more generic or on the contrary to be more specific.

This documentation is very minimalist and a full documentation will be available soon. The testing suite is even more minimalist and it will be improved to cover 100% of features.

## Installation

```
pip install python-jsonrepo
```

## Usage

### In process memory
 
``` python
import datetime
from jsonrepo.record import NamedtupleRecord
from jsonrepo.repository import Repository

fields = ['title', 'content']


class Message(namedtuple('Message', fields),
              NamedtupleRecord):
    """
    Example of namedtuple based record
    """
    def __new__(cls, **kwargs):
        default = {f: None for f in fields}
        default.update(kwargs)
        return super(Message, cls).__new__(cls, **default)


class MessagesRepository(Repository):
    prefix = 'messages'
    klass = Message


# make a singleton for our repository
my_repository = MessagesRepository()
msg1 = Message(title='Message1',
               content='and this is the content')
msg2 = Message(title='Message2',
               content='and this is the content')
now1 = datetime.datetime.utcnow().isoformat()[:-3]
my_repository.save('user-messages',
                   now1, msg1)
now2 = datetime.datetime.utcnow().isoformat()[:-3]
my_repository.save('user-messages',
                   now2, msg2)
record2 = my_repository.latest('user-messages')
record1 = my_repository.get('user-messages', now1)
records1 = my_repository.history('user-messages')
records2 = my_repository.history('user-messages', _from=now1)
records3 = my_repository.history('user-messages', _to=now2, _desc=False)
now3 = datetime.datetime.utcnow().isoformat()[:-3]
records4 = my_repository.history('user-messages', _from=now1, _to=now3)
```

### Redis

`REDIS_HOST`, `REDIS_PORT` and `REDIS_DB` environment variables will
be used to define access to a Redis server.

```python
class MessagesRepository(Repository):
    prefix = 'messages'
    klass = Message
    backend = 'redis'
```

### DynamoDB

Amazon AWS must configured.
The `prefix` value points at a table name on DynamoDB service of Amazon AWS.
Names of key and sort_key must configured.

```python
class MessagesRepository(Repository):
    prefix = 'messages'
    klass = Message
    backend = 'dynamodb'
    key = 'KEY'
    sort_key = 'DATE'
```

