# Python Library for [VIZ](https://github.com/VIZ-Blockchain/)

[![Documentation Status](https://readthedocs.org/projects/viz-python-lib/badge/?version=latest)](https://viz-python-lib.readthedocs.io/en/latest/?badge=latest)

**This library is in alpha state, API unstable**

Built on top of [python-graphenelib](https://github.com/xeroc/python-graphenelib/)

## Installation

Dependencies:

```
sudo apt-get install libffi-dev libssl-dev python-dev
```

Current published version could be installed via

```
pip install viz-python-lib
```

Manual installation:

Install [poetry](https://python-poetry.org/docs/)

```
cd viz-python-lib/
poetry install
```

## Basic read query example:

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
