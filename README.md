# Python Library for [VIZ](https://github.com/VIZ-Blockchain/)

This library is built on top of [python-graphenelib](https://github.com/xeroc/python-graphenelib/)

**This library is in alpha state**

**Installation**

```
$ sudo apt-get install g++ libboost-all-dev libssl-dev python3-pip
$ pip3 install setuptools
$ pip3 install graphenelib pycryptodome websockets appdirs Events scrypt pyyaml toolz funcy
$ git clone https://github.com/VIZ-Blockchain/viz-python-lib
$ cd viz-python-lib/
```

**Basic read query:**

```python
from viz import Client
from pprint import pprint

node = 'wss://solox.world/ws'

viz = Client(node=node)
pprint(viz.info())
```

Direct RPC calls:
```
viz.rpc.some_rpc_method()
```
