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


url = "wss://ws.viz.ropox.app"
SqliteConfigurationStore.setdefault("node", url)


def get_default_config_store(*args, **kwargs):
    if "appname" not in kwargs:
        kwargs["appname"] = "viz"
    return SqliteConfigurationStore(*args, **kwargs)


def get_default_key_store(config, *args, **kwargs):
    if "appname" not in kwargs:
        kwargs["appname"] = "viz"
    return SqliteEncryptedKeyStore(config=config, **kwargs)
