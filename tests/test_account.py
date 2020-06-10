import time

import pytest

from viz.account import Account
from viz.exceptions import AccountDoesNotExistsException


@pytest.fixture()
def account(viz, default_account):
    return Account(default_account)


@pytest.fixture(scope='session')
def _make_ops(viz, default_account):
    # Sent to different destinations to avoid transaction dupe check fail
    dests = ['null', 'alice', 'bob']
    for dest in dests:
        viz.transfer(dest, 1, "VIZ", memo="test", account=default_account)

    viz.transfer_to_vesting(10, account=default_account)
    time.sleep(1)


def test_init(viz, default_account):
    Account(default_account)

    with pytest.raises(AccountDoesNotExistsException):
        Account('dfsdsffdfdfd')


def test_balances(account):
    balance = account.balances
    assert balance['VIZ'] > 0


def test_energy(account):
    en = account.energy
    assert 0 < en <= 100


def test_current_energy(account, viz):
    en = account.current_energy()
    assert 0 < en <= 100

    pct = 10
    time.sleep(3)  # wait for HF4 on testnet
    viz.award(account.name, pct, account=account.name)
    en_new = account.current_energy()
    time.sleep(1)
    assert en - en_new == pytest.approx(pct, abs=1)


def test_virtual_op_count(viz):
    account = Account('committee')
    count = account.virtual_op_count()
    assert count > 0


def test_get_withdraw_routes(viz):
    name = 'alice'
    account = Account(name)
    viz.set_withdraw_vesting_route("bob", account=name)
    routes = account.get_withdraw_routes()
    assert routes[0]['from_account'] == name


@pytest.mark.usefixtures('_make_ops')
def test_history(account):
    history = list(account.history())
    assert 'trx_id' in history[0]

    history = list(account.history(raw_output=True))
    assert 'trx_id' in history[0][1]

    history = list(account.history(batch_size=1, limit=2))
    assert len(history) == 2

    history = list(account.history(filter_by='transfer_to_vesting'))
    assert history[0]['type'] == 'transfer_to_vesting'


@pytest.mark.usefixtures('_make_ops')
def test_history_reverse(account):
    history = list(account.history_reverse(batch_size=1, limit=2))
    assert len(history) == 2
