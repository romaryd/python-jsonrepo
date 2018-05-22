"""
Test Json repository
Author: Romary Dupuis <romary@me.comn>
"""
import os
import unittest
from collections import namedtuple
import datetime
import time
from jsonrepo.repository import Repository
from jsonrepo.record import NamedtupleRecord


try:
    from unittest import mock
except ImportError:
    import mock

fields = ['title', 'content', 'date', 'ttl']

os.environ['AWS_DEFAULT_REGION'] = 'eu-west-1'


class Message(namedtuple('Message', fields),
              NamedtupleRecord):
    """
    Example of namedtuple based record
    """
    def __new__(cls, **kwargs):
        default = {f: None for f in fields}
        default.update(kwargs)
        if default['date'] is None:
            default['date'] = datetime.datetime.utcnow().isoformat()[:-3]
        if default['ttl'] is None:
            default['ttl'] = int(time.mktime(time.strptime(
                default['date'], "%Y-%m-%dT%H:%M:%S.%f")))
        return super(Message, cls).__new__(cls, **default)


class MyRepository(Repository):
    prefix = 'example'
    klass = Message
    secondary_indexes = ['title', 'ttl']
    key = 'key'
    sort_key = 'date'


class RepositoryDictTests(unittest.TestCase):
    """
    Tests Repository class based on in memory process dictionary
    implementatiopn.
    """

    def test_singleton(self):
        """
        Assert singleton for repository
        """
        repo1 = MyRepository()
        repo2 = MyRepository()
        self.assertEqual(repo1, repo2)
        self.assertEqual(id(repo1), id(repo2))

    def test_save_record(self):
        """
        Assert that a json serializable record is properly saved
        """
        my_repository = MyRepository()
        msg = Message(title='This is a title',
                      content='and this is the content')
        now = datetime.datetime.utcnow().isoformat()[:-3]
        res = my_repository.save('test_save_record',
                                 now, msg)
        self.assertTrue(res)
        my_repository.delete('test_save_record', now)

    def test_get_record(self):
        """
        Assert that a json serializable record is retrieved
        """
        my_repository = MyRepository()
        msg = Message(title='This is a title',
                      content='and this is the content')
        now = datetime.datetime.utcnow().isoformat()[:-3]
        res = my_repository.save('test_get_record',
                                 now, msg)
        self.assertTrue(res)
        record = my_repository.get('test_get_record', now)
        self.assertEqual(record.title, msg.title)
        self.assertEqual(record.content, msg.content)
        my_repository.delete('test_get_record', now)

    def test_delete_record(self):
        """
        Assert delete a record
        """
        my_repository = MyRepository()
        msg = Message(title='This is a title',
                      content='and this is the content')
        now = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_delete_record',
                           now, msg)
        my_repository.delete('test_delete_record', now)
        result = my_repository.find('title', 'This is a title')
        self.assertEqual(result['count'], 0)

    def test_find_record(self):
        """
        Assert find a record
        """
        my_repository = MyRepository()
        msg = Message(title='This is a title',
                      content='and this is the content')
        now = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_find_record',
                           now, msg)
        result = my_repository.find('title', 'This is a title')
        self.assertEqual(result['count'], 1)
        self.assertEqual(result['items'][0].content, msg.content)
        my_repository.delete('test_find_record', now)

    def test_latest_record(self):
        """
        Assert that latest record
        """
        my_repository = MyRepository()
        msg1 = Message(title='Message1',
                       content='and this is the content')
        msg2 = Message(title='Message2',
                       content='and this is the content')
        now1 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_latest_record',
                           now1, msg1)
        time.sleep(1)
        now2 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_latest_record',
                           now2, msg2)
        record = my_repository.latest('test_latest_record')
        self.assertEqual(record.title, msg2.title)
        my_repository.delete('test_latest_record', now1)
        my_repository.delete('test_latest_record', now2)

    def test_history(self):
        """
        Assert history of records
        """
        my_repository = MyRepository()
        msg1 = Message(title='Message1',
                       content='and this is the content')
        msg2 = Message(title='Message2',
                       content='and this is the content')
        now1 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_history',
                           now1, msg1)
        time.sleep(1)
        now2 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('test_history',
                           now2, msg2)
        record = my_repository.latest('test_history')
        self.assertEqual(record.title, msg2.title)
        my_repository.delete('test_history', now1)
        my_repository.delete('test_history', now2)
