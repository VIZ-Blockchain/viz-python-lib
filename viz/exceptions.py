# -*- coding: utf-8 -*-
class BaseException(Exception):
    """Base excepsion class."""


class RPCConnectionRequired(BaseException):
    """An RPC connection is required."""


class AccountExistsException(BaseException):
    """The requested account already exists."""


class ObjectNotInProposalBuffer(BaseException):
    """Object was not found in proposal."""


class HtlcDoesNotExistException(BaseException):
    """HTLC object does not exist."""
