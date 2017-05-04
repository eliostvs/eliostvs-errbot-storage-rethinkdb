import logging
from os.path import abspath, dirname, join
from unittest import mock

import jsonpickle
import pytest
import rethinkdb as r
from errbot.backends.test import testbot

from rethinkdbstorage import DB_NAME, DatabaseUtils, RethinkDBStorage, RethinkDBPlugin

HERE = dirname(abspath(__file__))
_ = testbot
extra_plugin_dir = join(HERE, 'plugins')
TABLE_NAME = 'ns'


@pytest.fixture(scope='module')
def conn():
    return r.connect(port=pytest.config.getoption('port'))


def run_query(query, conn):
    try:
        return query.run(conn)
    except Exception as ex:
        logging.exception(ex)


@pytest.fixture
def db_admin(conn):
    return DatabaseUtils.from_connection(conn)


def setup_module():
    db_drop(conn())
    db_create(conn())


def teardown_module():
    db_drop(conn())


def table_create(conn):
    run_query(r.db(DB_NAME).table_create(TABLE_NAME), conn)


def setup_function():
    table_drop(conn())
    table_create(conn())


def teardown_function():
    table_drop(conn())


@pytest.fixture
def storage(conn):
    return RethinkDBStorage(conn, TABLE_NAME)


def db_list(conn):
    return run_query(r.db_list(), conn)


def db_drop(conn):
    run_query(r.db_drop(DB_NAME), conn)


def db_create(conn):
    run_query(r.db_create(DB_NAME), conn)


def table_list(conn):
    return run_query(r.db(DB_NAME).table_list(), conn)


def table_drop(conn):
    run_query(r.db(DB_NAME).table(TABLE_NAME).delete(), conn)


def insert_value(conn, kv):
    return run_query(r.db(DB_NAME).table(TABLE_NAME).insert(kv), conn)


def test_setup_connection(conn, db_admin):
    db_drop(conn)

    db_admin.setup(TABLE_NAME)

    assert DB_NAME in db_list(db_admin.conn)
    assert TABLE_NAME in table_list(db_admin.conn)


def test_setup_connection_through_plugin(conn):
    bot_config = mock.Mock(STORAGE_CONFIG={'port': conn.port})

    plugin = RethinkDBPlugin(bot_config)
    storage = plugin.open(TABLE_NAME)

    assert isinstance(storage, RethinkDBStorage)
    assert storage.table_name == TABLE_NAME

    assert DB_NAME in db_list(storage.conn)
    assert TABLE_NAME in table_list(storage.conn)


def test_storage_get_should_work(storage):
    key = 'foo'
    value = jsonpickle.encode('bar')

    insert_value(storage.conn, {'id': key, 'value': value})

    assert storage.get(key) == jsonpickle.decode(value)


def test_storage_get_should_raise_key_error(storage):
    with pytest.raises(KeyError) as ex:
        storage.get("foo")

        assert str(ex) == "foo doesn't exists"


def test_storage_set_should_work(storage):
    key = 'foo'
    value = 'bar'

    storage.set(key, value)

    expected = {'id': key, 'value': jsonpickle.encode(value)}
    actual = r.db(DB_NAME).table(TABLE_NAME).get('foo').run(storage.conn)

    assert actual == expected


class MyClass:
    pass


def test_should_be_capable_of_save_and_return_complex_object(storage):
    storage.set('clazz', MyClass())

    assert type(storage.get('clazz')) == MyClass


def test_remove_key_should_work(storage):
    key = 'foo'

    insert_value(storage.conn, {'id': key, 'value': 'value'})

    storage.remove(key)


def test_remove_key_should_fail(storage):
    with pytest.raises(KeyError) as ex:
        storage.remove("foo")

        assert str(ex) == "foo doesn't exists"


def test_storage_return_number_of_items(storage):
    insert_value(storage.conn, {'id': 'foo', 'value': 'value'})
    insert_value(storage.conn, {'id': 'bar', 'value': 'value'})
    insert_value(storage.conn, {'id': 'zap', 'value': 'value'})

    assert storage.len() == 3


def test_storage_return_list_of_keys(storage):
    insert_value(storage.conn, {'id': 'foo', 'value': 'value'})
    insert_value(storage.conn, {'id': 'zap', 'value': 'value'})

    assert sorted(storage.keys()) == sorted(['foo', 'zap'])


def test_storage_close_should_to_nothing(storage):
    assert storage.close() is None


def test_command(testbot):
    testbot.assertCommand('!teststorage', 'OK')
