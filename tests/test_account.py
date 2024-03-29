import time
import pytest
from graphenecommon.exceptions import AccountDoesNotExistsException
from viz.account import Account


@pytest.fixture()
def account(viz, default_account):
    return Account(default_account)


@pytest.fixture(scope='session')
def _make_ops(viz, default_account):
    # Sent to different destinations to avoid transaction dupe check fail
    dests = ['null', 'alice', 'bob']
    for dest in dests:
        viz.transfer(dest, 1, "VIZ", memo="test_account", account=default_account)

    viz.transfer_to_vesting(10, account=default_account)
    time.sleep(1)


def test_account_not_found(viz, default_account):
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
    time.sleep(15)  # wait for HF4 on testnet
    viz.award(account.name, pct, account=account.name)
    time.sleep(1)
    en_new = account.current_energy()
    assert en - en_new == pytest.approx(pct, abs=5.0)


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
def test_history_reverse(account: Account):
    time.sleep(2)
    history = list(account.history_reverse(batch_size=1, limit=2))
    assert len(history) == 2
