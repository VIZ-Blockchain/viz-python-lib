import pytest

from viz.exceptions import AccountExistsException
from vizbase.account import PrivateKey


@pytest.fixture()
def _add_liquid_to_alice(viz, default_account):
    viz.transfer('alice', 1000, 'VIZ', account=default_account)


def test_info(viz):
    viz.info()


def test_new_proposal(viz, default_account):
    proposal = viz.new_proposal('title', 'test proposal', account='alice')
    viz.transfer("null", 1, "VIZ", memo="test transfer proposal", account=default_account, append_to=proposal)
    proposal.broadcast()
    proposals = viz.rpc.get_proposed_transactions('alice', 0, 100)
    assert len(proposals) > 0


def test_proposal_update(viz, default_account):
    proposer = 'alice'
    title = 'test update 1'
    proposal = viz.new_proposal(title, account=proposer)
    viz.transfer("null", 1, "VIZ", memo="test_proposal_update", account=default_account, append_to=proposal)
    proposal.broadcast()
    viz.proposal_update(proposer, title, approve=True, permission='active', account=default_account)
    # TODO: need multisig to test disapproval; fix after implementing viz.allow()
    # viz.proposal_update(proposer, title, approve=False, permission='active', account=default_account)


def test_transfer(viz, default_account):
    trx = viz.transfer("null", 1, "VIZ", memo="test_viz", account=default_account)
    assert isinstance(trx, dict)
    viz.transfer(default_account, 1, "VIZ", memo="#encrypted memo", account=default_account)


def test_award(viz, default_account):
    viz.award(default_account, 10, memo="test_viz", account=default_account)

    beneficiaries = [{"account": default_account, "weight": 50}]
    viz.award(default_account, 10, memo="test_viz", beneficiaries=beneficiaries, account=default_account)


@pytest.mark.skip(reason="too long to wait HF 11")
def test_fixed_award(viz, default_account):
    yield
    viz.fixed_award(default_account, reward_amount=10, max_energy=50, memo="test_viz", account=default_account)

    beneficiaries = [{"account": default_account, "weight": 50}]
    viz.fixed_award(
        default_account,
        reward_amount=10,
        max_energy=50,
        memo="test_viz",
        beneficiaries=beneficiaries,
        account=default_account,
    )


def test_custom(viz, default_account):
    custom = {"foo": "bar"}
    viz.custom("a", custom, required_active_auths=[default_account])

    custom = {"foo": "baz"}
    viz.custom("a", custom, required_regular_auths=[default_account])


def test_withdraw_vesting(viz):
    viz.withdraw_vesting(10, account="alice")


def test_transfer_to_vesting(viz, default_account):
    viz.transfer_to_vesting(10, to="alice", account=default_account)


def test_set_withdraw_vesting_route(viz):
    viz.set_withdraw_vesting_route("bob", account="alice")


def test_get_withdraw_vesting_routes(viz):
    viz.get_withdraw_vesting_routes("bob")


@pytest.mark.usefixtures('_add_liquid_to_alice')
def test_create_account(viz):
    # normal case
    viz.create_account('jimmy', password='123', creator='alice')

    # invalid args
    with pytest.raises(ValueError, match='Account name must be at most'):
        viz.create_account('longname' * 100, password='123', creator='alice')

    with pytest.raises(ValueError, match='You cannot use'):
        viz.create_account('jimmy', password='123', active_key='wtf', creator='alice')

    with pytest.raises(ValueError, match="Call incomplete! Provide either a password or public keys!"):
        viz.create_account('jimmy2', creator='alice')

    with pytest.raises(AccountExistsException):
        viz.create_account('bob', password='123', creator='alice')

    # manually provide keys
    pubkeys = [format(PrivateKey().pubkey, viz.prefix) for _ in range(0, 4)]
    viz.create_account(
        'jimmy3',
        creator='alice',
        master_key=pubkeys[0],
        active_key=pubkeys[1],
        regular_key=pubkeys[2],
        memo_key=pubkeys[3],
    )

    # additional key and account auths
    viz.create_account(
        'jimmy4',
        password='123',
        creator='alice',
        additional_master_keys=[pubkeys[0]],
        additional_active_keys=[pubkeys[1]],
        additional_regular_keys=[pubkeys[2]],
    )
    viz.create_account(
        'jimmy5',
        password='123',
        creator='alice',
        additional_master_accounts=['bob'],
        additional_active_accounts=['bob'],
        additional_regular_accounts=['bob'],
    )

    # custom fee and delegation
    viz.create_account('jimmy6', password='123', creator='alice', fee=5)
    viz.create_account('jimmy7', password='123', creator='alice', delegation=100)

    # referrer
    viz.create_account('jimmy8', password='123', creator='alice', referrer='bob')


def test_delegate_vesting_shares(viz):
    viz.delegate_vesting_shares(delegator='alice', delegatee='bob', amount=10)
