import logging
from typing import Any, List, Dict

import jsonpickle
import rethinkdb as r
from errbot.storage.base import StorageBase, StoragePluginBase

logger = logging.getLogger('errbot.storage.rethinkdb')

DB_NAME = 'errbot_storage'


class StorageException(Exception):
    pass


class DatabaseUtils:
    @staticmethod
    def from_connection(connection):
        return DatabaseUtils(connection)

    @staticmethod
    def from_args(kwargs: Dict[str, Any]):
        connection = r.connect(**kwargs)
        return DatabaseUtils(connection)

    def __init__(self, conn: r.Connection):
        self.conn = conn

    def setup(self, table_name: str):
        if self._database_not_exist():
            self._create_database()

        if self._table_not_exist(table_name):
            self._create_table(table_name)

    def _create_database(self) -> None:
        logger.debug('action=createDatabase name=%s', DB_NAME)

        result = r.db_create(DB_NAME).run(self.conn)

        assert result['dbs_created'] == 1, StorageException('Create database %s failed' % DB_NAME)

    def _create_table(self, table_name: str) -> None:
        logger.debug('action=createTable name=%s', table_name)

        result = r.db(DB_NAME).table_create(table_name).run(self.conn)

        assert result['tables_created'] == 1, StorageException(
            'Create table {} failed'.format(table_name))

    def _table_not_exist(self, table_name: str) -> bool:
        return table_name not in r.db(DB_NAME).table_list().run(self.conn)

    def _database_not_exist(self) -> bool:
        return DB_NAME not in r.db_list().run(self.conn)


class RethinkDBStorage(StorageBase):
    def __init__(self, connection, table_name):
        self.conn = connection
        self.table_name = table_name

    def get(self, key: str) -> Any:
        logger.debug('action=getKey key=%s', key)

        try:
            item = self.table.get(key).get_field('value').run(self.conn)
            return jsonpickle.decode(item)

        except r.ReqlNonExistenceError as e:
            raise KeyError("%s doesn't exists." % key)

    def remove(self, key: str) -> None:
        logger.debug('action=removeKey key=%s', key)

        result = self.table.get(key).delete().run(self.conn)

        if not result or result['deleted'] != 1:
            raise KeyError("%s doesn't exists." % key)

    def set(self, key: str, value: Any) -> None:
        encoded_value = jsonpickle.encode(value)

        logger.debug('action=addKey name=%s value=%s', key, encoded_value)

        result = self.table.insert({'id': key, 'value': encoded_value}, conflict="update").run(self.conn)

        assert self._was_successful(result) is True, StorageException("key %s not inserted " % key)

    @staticmethod
    def _was_successful(result):
        return any([result['inserted'], result['replaced'], result['unchanged']])

    def len(self) -> int:
        return self.table.count().run(self.conn)

    def keys(self) -> List[str]:
        return self.table.get_field('id').run(self.conn)

    def close(self) -> None:
        pass

    @property
    def table(self):
        return r.db(DB_NAME).table(self.table_name)


class RethinkDBPlugin(StoragePluginBase):
    def open(self, namespace: str) -> StorageBase:
        config = self._storage_config

        db_utils = DatabaseUtils.from_args(config)
        db_utils.setup(namespace)

        return RethinkDBStorage(db_utils.conn, namespace)
