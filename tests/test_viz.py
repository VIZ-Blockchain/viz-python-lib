def test_info(viz):
    viz.info()


def test_transfer(viz, default_account):

    viz.transfer("null", 1, "VIZ", memo="test", account=default_account)
    viz.transfer(default_account, 1, "VIZ", memo="#encrypted memo", account=default_account)
