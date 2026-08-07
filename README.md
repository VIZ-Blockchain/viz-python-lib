# Python Library for [VIZ](https://github.com/VIZ-Blockchain)

![Tests Status](https://github.com/VIZ-Blockchain/viz-python-lib/actions/workflows/tests.yml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/viz-python/badge/?version=latest)](https://viz-python.readthedocs.io/en/latest/?badge=latest)

## Usage examples

### Award someone

```python
from viz import Client

node = "wss://node.viz.cx/ws"
viz = Client(node=node, keys=["5...your_private_regular_key..."])

initiator = "your_account"
receiver = "id"
percent = 10.5 # 10.5%
viz.award(receiver, percent, "with love", None, initiator)
```

### Award someone with fixed reward

```python
from viz import Client

node = "wss://node.viz.cx/ws"
viz = Client(node=node, keys=["5...your_private_regular_key..."])

initiator = "your_account"
receiver = "id"
reward_amount = 3.5 # "3.50 VIZ"
max_energy = 30 # 30%
viz.fixed_award(receiver, reward_amount, max_energy, "with fixed reward", None, initiator)
```

### Send a custom operation

```python
from viz import Client

node = "wss://node.viz.cx/ws"
viz = Client(node=node, keys=["5...your_private_regular_key..."])

account = "your_account"
required_regular_auths = [account]
protocol = "color.place"
custom_json = {"x": 35, "y": 70, "color": "#e50000"}
viz.custom(protocol, custom_json, None, required_regular_auths)
```

### Prediction market operations (HF14 / Onix)

All 23 broadcastable `pm_*` operations are available as serializers in
`vizbase.operations`. Build the operation and sign it with `finalizeOp` (the
same low-level path the built-in helpers use), passing the authority the op
requires — `active` for most PM ops, `regular` for `pm_dispute_vote`:

```python
from viz import Client
from vizbase import operations

node = "wss://node.viz.cx/ws"
viz = Client(node=node, keys=["5...your_private_active_key..."])

account = "your_account"

# Place a bet: binary market -> side 0/1, outcome_index -1; multi -> side -1, outcome_index 0..N-1
bet = operations.Pm_place_bet(
    account=account,
    market_id=42,
    side=1,
    outcome_index=-1,
    amount="1.500 VIZ",
    min_tokens=0,  # slippage floor (0 = none)
    mode=0,        # 0 instant, 1 batch
)
viz.finalizeOp(bet, account, "active")
```

Chain governance uses the versioned variant: `versioned_chain_properties_update`
serializes variant 3 (`chain_properties_hf9`), 4 (`chain_properties_hf13`) or 5
(`chain_properties_pm`, the HF14 PM params) automatically from the fields you pass.

### Get data from custom protocol

```python
from viz import Client
from viz.account import Account
from viz.block import Block
from viz.instance import set_shared_blockchain_instance
import json

viz = Client("wss://node.viz.cx/ws")
set_shared_blockchain_instance(viz)

account_name = "id"
protocol = "V"
account = Account(account_name, protocol=protocol)

counter_inside_protocol = account["custom_sequence"]
last_used_in_block = account["custom_sequence_block_num"]

block = Block(last_used_in_block)

for tx in block["transactions"]:
    for op_type, op_data in tx["operations"]:
        if op_type != "custom":
            continue
        if op_data.get("id") != protocol:
            continue
        if account_name not in op_data.get("required_regular_auths", []):
            continue

        raw_json = op_data.get("json")
        try:
            json_from_protocol = json.loads(raw_json) if raw_json else None
        except json.JSONDecodeError:
            json_from_protocol = None

        print(json_from_protocol)
```

### Any direct RPC call

```python
from viz import Client

viz = Client("wss://node.viz.cx/ws")
viz.rpc.get_dynamic_global_properties()
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

## Development

### Dependencies

#### Linux dependencies

```sh
sudo apt-get install libffi-dev libssl-dev python3-dev
```

#### Windows dependencies

Install regular version of [OpenSSL](https://slproweb.com/products/Win32OpenSSL.html) (not Light) suitable for your core processor.

#### MacOS dependencies

Apple has deprecated use of OpenSSL in favor of its own TLS and crypto libraries. This means that you will need to install and export some OpenSSL settings yourself, before you can install viz-python-lib:

```sh
brew install openssl
```

and then use the following commands:

```sh
export CFLAGS="-I$(brew --prefix openssl)/include"
export LDFLAGS="-L$(brew --prefix openssl)/lib"
```
