import pytest

from viz.amount import Amount


@pytest.fixture()
def amount():
    return Amount("10 VIZ")


def test_init():
    amount = Amount("10 VIZ")
    Amount(amount)


def test_properties(amount):
    assert amount.amount == 10
    assert amount.symbol == "VIZ"
    assert amount.asset == "VIZ"


def test_str(amount):
    assert str(amount) == "10.000 VIZ"


def test_add(amount):
    am = Amount("2 VIZ")
    _sum = amount + am
    assert float(_sum) == 12
