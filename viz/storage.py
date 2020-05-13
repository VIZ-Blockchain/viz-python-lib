# -*- coding: utf-8 -*-
from graphenestorage import (
    InRamConfigurationStore,
    InRamEncryptedKeyStore,
    InRamPlainKeyStore,
    SqliteConfigurationStore,
    SqliteEncryptedKeyStore,
    SQLiteFile,
    SqlitePlainKeyStore,
)

from vizbase.chains import DEFAULT_PREFIX

url = "wss://ws.viz.ropox.app"
SqliteConfigurationStore.setdefault("node", url)
appname = DEFAULT_PREFIX.lower()


def get_default_config_store(*args, **kwargs):
    if "appname" not in kwargs:
        kwargs["appname"] = appname
    return SqliteConfigurationStore(*args, **kwargs)


def get_default_key_store(config, *args, **kwargs):
    if "appname" not in kwargs:
        kwargs["appname"] = appname
    return SqliteEncryptedKeyStore(config=config, **kwargs)
