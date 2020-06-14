from grapheneapi.exceptions import RPCError


def decode_rpc_error_msg(exc: Exception) -> str:
    r"""
    Helper function to decode the raised Exception and give it a python Exception class.

    Exception text usually consists of two lines, in raw:

    ``Assert Exception (10)\namount.amount > 0: Cannot transfer a negative amount (aka: stealing)\n\n``
    or

    ``missing required active authority (3010000)\nMissing Active Authority ["viz"]\n\n\n``

    We're omitting the fist line and returning meaningful second line, stripping trailing newlines.
    """
    lines = str(exc).strip("\n").split("\n")
    return lines[-1]


class MissingRequiredAuthority(RPCError):
    pass


class NoSuchAPI(RPCError):
    pass


class UnhandledRPCError(RPCError):
    pass


class ReadLockFail(RPCError):
    pass


class UnknownNetwork(RPCError):
    pass
