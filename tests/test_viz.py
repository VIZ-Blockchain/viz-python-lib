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
    viz.proposal_update(proposer, title, approve=True, permission='active', account=default_account)
    # TODO: need multisig to test disapproval
    # viz.proposal_update(proposer, title, approve=False, permission='active', account=default_account)


def test_transfer(viz, default_account):

    trx = viz.transfer("null", 1, "VIZ", memo="test_viz", account=default_account)
    assert isinstance(trx, dict)
    viz.transfer(default_account, 1, "VIZ", memo="#encrypted memo", account=default_account)


def test_award(viz, default_account):
    viz.award(default_account, 10, memo="test_viz", account=default_account)

    beneficiaries = [{"account": default_account, "weight": 50}]
    viz.award(default_account, 10, memo="test_viz", beneficiaries=beneficiaries, account=default_account)


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
