import json
import boto3
from boto3.dynamodb.conditions import Key
from loggingmixin import LoggingMixin
from awesomedecorators import memoized
from jsonrepo.backend import Backend


class DynamoDBBackend(Backend, LoggingMixin):
    """
    Backend based on DynamoDB
    """

    def __init__(self, prefix, key, sort_key,
                 secondary_indexes):
        self._prefix = prefix
        self._key = key
        self._sort_key = sort_key
        self._secondary_indexes = secondary_indexes

    @memoized
    def dynamodb_server(self):
        dynamodb = boto3.resource('dynamodb')
        return dynamodb.Table(self._prefix)

    def get(self, key, sort_key):
        self.logger.debug('Storage - get {}'.format(self.prefixed(key)))
        res = self.dynamodb_server.get_item(Key={
            self._key: self.prefixed(key),
            self._sort_key: sort_key
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
        obj = json.loads(value)
        for index in self._secondary_indexes:
            if obj.get(index, None) not in ['', None]:
                item.update({
                    index: obj[index]
                })
        if sort_key is not None:
            item.update({
                self._sort_key: sort_key
            })
        return self.dynamodb_server.put_item(Item=item)

    def delete(self, key, sort_key):
        self.logger.debug('Storage - delete {}'.format(self.prefixed(key)))
        return self.dynamodb_server.delete_item(Key={
            self._key: self.prefixed(key),
            self._sort_key: sort_key
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
        self.logger.debug('Storage - get latest for {}'.format(
            self.prefixed(key)
        ))
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

    def find(self, index, value):
        res = self.dynamodb_server.query(
            KeyConditionExpression=Key(index).eq(value),
            IndexName='{}-index'.format(index)
        )
        self.logger.debug('{}'.format(res))
        return {
            'count': res['Count'],
            'items': [item['value'] for item in res['Items']]
        }
