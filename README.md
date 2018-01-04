# jsonrepo

[![Build Status](https://travis-ci.org/romaryd/python-jsonrepo.svg?branch=master)](https://travis-ci.org/romaryd/python-jsonrepo)
[![Coverage Status](https://coveralls.io/repos/github/romaryd/python-jsonrepo/badge.svg?branch=master)](https://coveralls.io/github/romaryd/python-jsonrepo?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/5d394fb9d6a3d88500ba/maintainability)](https://codeclimate.com/github/romaryd/python-jsonrepo/maintainability)
[![Code Health](https://landscape.io/github/romaryd/python-jsonrepo/master/landscape.svg?style=flat)](https://landscape.io/github/romaryd/python-jsonrepo/master)

---
A simple repository for json serializable objects.

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

my_repository = MyRepository()
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
records = my_repository.history('user-messages')
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

