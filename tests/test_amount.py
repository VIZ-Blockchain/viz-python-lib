import pytest

from viz.amount import Amount


@pytest.fixture()
def amount():
    return Amount("10 VIZ")


def test_init():
    amount = Amount("10 VIZ")
    Amount(amount)


def test_init_default():
    assert Amount().amount == 0
    assert Amount().symbol == "VIZ"


def test_init_invalid_type():
    with pytest.raises(ValueError):
        Amount(10)


def test_properties(amount):
    assert amount.amount == 10
    assert amount.symbol == "VIZ"
    assert amount.asset == "VIZ"


def test_str(amount):
    assert str(amount) == "10.000 VIZ"


def test_repr_matches_str(amount):
    assert repr(amount) == str(amount)


def test_int_and_float(amount):
    assert int(amount) == 10
    assert float(amount) == 10.0


def test_add(amount):
    am = Amount("2 VIZ")
    _sum = amount + am
    assert float(_sum) == 12


def test_add_does_not_mutate_operands(amount):
    other = Amount("2 VIZ")
    amount + other
    assert amount.amount == 10
    assert other.amount == 2


def test_add_scalar(amount):
    assert float(amount + 5) == 15


def test_add_mismatched_asset_raises(amount):
    with pytest.raises(AssertionError):
        amount + Amount("1 SHARES")


def test_sub(amount):
    assert float(amount - Amount("3 VIZ")) == 7


def test_mul_scalar(amount):
    assert float(amount * 2) == 20


def test_floordiv_scalar(amount):
    assert float(amount // 3) == 3


def test_floordiv_amount_raises(amount):
    with pytest.raises(ValueError):
        amount // Amount("2 VIZ")


def test_iadd_mutates(amount):
    amount += Amount("5 VIZ")
    assert amount.amount == 15


def test_comparisons(amount):
    assert amount > Amount("5 VIZ")
    assert amount >= Amount("10 VIZ")
    assert amount == Amount("10 VIZ")
    assert amount != Amount("9 VIZ")
    assert amount < Amount("11 VIZ")
    assert amount <= Amount("10 VIZ")


def test_compare_with_scalar(amount):
    assert amount == 10
    assert amount > 5
    assert amount < 20


def test_compare_with_none(amount):
    assert amount > None
    assert (amount == None) is False  # noqa: E711
