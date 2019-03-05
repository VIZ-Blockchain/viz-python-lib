# Python Library for [VIZ](https://github.com/VIZ-Blockchain/)

This library is built on top of [python-graphenelib](https://github.com/xeroc/python-graphenelib/)

**This library is in alpha state**

Basic read query:

```python
from viz import Client
from pprint import pprint

node = 'wss://ws.viz.ropox.app'

viz = Client(node=node)
pprint(viz.info())
```

Direct RPC calls:
```
viz.rpc.some_rpc_method()
```
