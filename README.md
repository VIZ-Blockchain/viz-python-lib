# Python Library for [VIZ](https://github.com/VIZ-Blockchain)

![tests](https://github.com/VIZ-Blockchain/viz-python-lib/workflows/tests/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/viz-python-lib/badge/?version=latest)](https://viz-python-lib.readthedocs.io/en/latest/?badge=latest)

**This library is in alpha state, API unstable**

Built on top of [python-graphenelib](https://github.com/xeroc/python-graphenelib/)

## Dependencies

#### Linux dependencies

```sh
sudo apt-get install libffi-dev libssl-dev python-dev
```

#### Windows dependencies

Install regular version of [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) (not Light) suitable for your core processor.

#### MacOS dependencies

Apple has deprecated use of OpenSSL in favor of its own TLS and crypto libraries. This means that you will need to install and export some OpenSSL settings yourself, before you can install viz-python-lib:

```sh
brew install openssl
```

and then use the following commands
```sh
export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"
```

## Installation

Current published version could be installed via

```sh
pip install viz-python-lib
```

Manual installation:

Install [poetry](https://python-poetry.org/docs/)

```sh
cd viz-python-lib/
poetry install
```

## Usage

Basic read query example:
```python
from viz import Client
from pprint import pprint

node = 'wss://node.viz.cx/ws'

viz = Client(node=node)
pprint(viz.info())
```

Direct RPC calls:
```python
viz.rpc.some_rpc_method()
```
