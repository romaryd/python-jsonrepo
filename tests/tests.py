"""
Test Json repository
Author: Romary Dupuis <romary@me.comn>
"""

import unittest
from collections import namedtuple
import datetime
from jsonrepo.repository import Repository
from jsonrepo.record import NamedtupleRecord


try:
    from unittest import mock
except ImportError:
    import mock

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


class MyRepository(Repository):
    prefix = 'example'
    klass = Message


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
        res = my_repository.save('message-one',
                                 now, msg)
        self.assertTrue(res)

    def test_get_record(self):
        """
        Assert that a json serializable record is retrieved
        """
        my_repository = MyRepository()
        msg = Message(title='This is a title',
                      content='and this is the content')
        now = datetime.datetime.utcnow().isoformat()[:-3]
        res = my_repository.save('message-one',
                                 now, msg)
        self.assertTrue(res)
        record = my_repository.get('message-one', now)
        self.assertEqual(record.title, msg.title)
        self.assertEqual(record.content, msg.content)

    def test_latest_record(self):
        """
        Assert that a record is deleted
        """
        my_repository = MyRepository()
        msg1 = Message(title='Message1',
                       content='and this is the content')
        msg2 = Message(title='Message2',
                       content='and this is the content')
        now1 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('user-message',
                           now1, msg1)
        now2 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('user-message',
                           now2, msg2)
        record = my_repository.latest('user-message')
        self.assertEqual(record.title, msg2.title)

    def test_history(self):
        """
        Assert that a record is deleted
        """
        my_repository = MyRepository()
        msg1 = Message(title='Message1',
                       content='and this is the content')
        msg2 = Message(title='Message2',
                       content='and this is the content')
        now1 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('user-message',
                           now1, msg1)
        now2 = datetime.datetime.utcnow().isoformat()[:-3]
        my_repository.save('user-message',
                           now2, msg2)
        record = my_repository.latest('user-message')
        self.assertEqual(record.title, msg2.title)
