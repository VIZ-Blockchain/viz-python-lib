def test_info(viz):
    viz.info()


def test_transfer(viz, default_account):

    trx = viz.transfer("null", 1, "VIZ", memo="test", account=default_account)
    assert isinstance(trx, dict)
    viz.transfer(default_account, 1, "VIZ", memo="#encrypted memo", account=default_account)


def test_decode_memo():
    # TODO
    pass


def test_award(viz, default_account):
    viz.award(default_account, 10, memo="test", account=default_account)

    beneficiaries = [{"account": default_account, "weight": 50}]
    viz.award(default_account, 10, memo="test", beneficiaries=beneficiaries, account=default_account)


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
