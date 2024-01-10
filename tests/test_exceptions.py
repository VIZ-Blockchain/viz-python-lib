import re

import pytest

from vizapi.exceptions import MissingRequiredAuthority, NoSuchAPI, UnhandledRPCError, decode_rpc_error_msg
from vizbase import operations


def test_decode_assert():
    msg = 'Assert Exception (10)\namount.amount > 0: Cannot transfer a negative amount (aka: stealing)\n\n'
    decoded = decode_rpc_error_msg(Exception(msg))
    assert decoded == 'amount.amount > 0: Cannot transfer a negative amount (aka: stealing)'


def test_decode_missing_active_authority():
    msg = 'missing required active authority (3010000)\nMissing Active Authority ["viz"]\n\n\n'
    decoded = decode_rpc_error_msg(Exception(msg))
    assert decoded == 'Missing Active Authority ["viz"]'


def test_missing_active_authority(viz, default_account):
    memo = 'test'
    op = operations.Transfer(
        **{"from": default_account, "to": default_account, "amount": "{}".format(str('-0.001 VIZ')), "memo": memo}
    )
    with pytest.raises(MissingRequiredAuthority, match=re.escape('Missing Active Authority ["viz"]')):
        viz.finalizeOp(op, default_account, "active")


def test_negative_transfer(viz, default_account):
    with pytest.raises(
        UnhandledRPCError, match=re.escape('amount.amount > 0: Cannot transfer a negative amount (aka: stealing)')
    ):
        viz.transfer("null", -1, "VIZ", memo="test", account=default_account)


def test_negative_withdraw(viz):
    with pytest.raises(UnhandledRPCError, match='vesting_shares.amount >= 0: Cannot withdraw negative SHARES'):
        viz.withdraw_vesting(-10, account="alice")


def test_negative_delegate_vesting_shares(viz):
    with pytest.raises(UnhandledRPCError, match='vesting_shares.amount >= 0: Delegation cannot be negative'):
        viz.delegate_vesting_shares(delegator='alice', delegatee='bob', amount=-10)


def test_self_delegate_vesting_shares(viz, default_account):
    with pytest.raises(UnhandledRPCError, match='delegator != delegatee: You cannot delegate SHARES to yourself'):
        viz.delegate_vesting_shares(delegator=default_account, delegatee=default_account, amount=10)


def test_too_much_beneficiaries(viz, default_account):
    beneficiaries = [{"account": default_account, "weight": 50}] * 256

    with pytest.raises(
        UnhandledRPCError, match=re.escape('beneficiaries.size() < 128: Cannot specify more than 127 beneficiaries')
    ):
        viz.award(default_account, 10, memo="test", beneficiaries=beneficiaries, account=default_account)


def test_unknown_method(viz):
    with pytest.raises(NoSuchAPI, match='^Cannot find API for you request'):
        viz.rpc.example_method()
