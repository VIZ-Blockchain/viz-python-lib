from vizbase.chains import PRECISIONS


class Amount(dict):
    """
    This class helps deal and calculate with the different assets on the chain.

    :param str amount_string: Amount string as used by the backend (e.g. "10 VIZ")
    """

    def __init__(self, amount_string="0 VIZ"):
        if isinstance(amount_string, Amount):
            self["amount"] = amount_string["amount"]
            self["asset"] = amount_string["asset"]
        elif isinstance(amount_string, str):
            self["amount"], self["asset"] = amount_string.split(" ")
        else:
            raise ValueError("Need an instance of 'Amount' or a string with amount and asset")

        self["amount"] = float(self["amount"])

    @property
    def amount(self):
        return self["amount"]

    @property
    def symbol(self):
        return self["asset"]

    @property  # noqa: CCE001
    def asset(self):
        return self["asset"]

    def __str__(self):
        prec = PRECISIONS.get(self["asset"], 6)
        return "{:.{prec}f} {}".format(self["amount"], self["asset"], prec=prec)

    def __float__(self):
        return self["amount"]

    def __int__(self):
        return int(self["amount"])

    def __add__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            am["amount"] += other["amount"]
        else:
            am["amount"] += float(other)
        return am

    def __sub__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            am["amount"] -= other["amount"]
        else:
            am["amount"] -= float(other)
        return am

    def __mul__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            am["amount"] *= other["amount"]
        else:
            am["amount"] *= other
        return am

    def __floordiv__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            raise ValueError("Cannot divide two Amounts")
        else:
            am["amount"] //= other
        return am

    def __div__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            raise ValueError("Cannot divide two Amounts")
        else:
            am["amount"] /= other
        return am

    def __mod__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            am["amount"] %= other["amount"]
        else:
            am["amount"] %= other
        return am

    def __pow__(self, other):
        am = Amount(self)
        if isinstance(other, Amount):
            am["amount"] **= other["amount"]
        else:
            am["amount"] **= other
        return am

    def __iadd__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] += other["amount"]
        else:
            self["amount"] += other
        return self

    def __isub__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            self["amount"] -= other["amount"]
        else:
            self["amount"] -= other
        return self

    def __imul__(self, other):
        if isinstance(other, Amount):
            self["amount"] *= other["amount"]
        else:
            self["amount"] *= other
        return self

    def __idiv__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] / other["amount"]
        else:
            self["amount"] /= other
            return self

    def __ifloordiv__(self, other):
        if isinstance(other, Amount):
            self["amount"] //= other["amount"]
        else:
            self["amount"] //= other
        return self

    def __imod__(self, other):
        if isinstance(other, Amount):
            self["amount"] %= other["amount"]
        else:
            self["amount"] %= other
        return self

    def __ipow__(self, other):
        self["amount"] **= other
        return self

    def __lt__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] < other["amount"]
        else:
            return self["amount"] < float(other or 0)

    def __le__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] <= other["amount"]
        else:
            return self["amount"] <= float(other or 0)

    def __eq__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] == other["amount"]
        else:
            return self["amount"] == float(other or 0)

    def __ne__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] != other["amount"]
        else:
            return self["amount"] != float(other or 0)

    def __ge__(self, other):
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] >= other["amount"]
        else:
            return self["amount"] >= float(other or 0)

    def __gt__(self, other):  # noqa: CCE001
        if isinstance(other, Amount):
            assert other["asset"] == self["asset"]
            return self["amount"] > other["amount"]
        else:
            return self["amount"] > float(other or 0)

    __repr__ = __str__
    __truediv__ = __div__
    __truemul__ = __mul__
