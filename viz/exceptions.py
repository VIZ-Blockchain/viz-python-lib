# -*- coding: utf-8 -*-
from graphenecommon.exceptions import (
    AccountDoesNotExistsException,
    AssetDoesNotExistsException,
    BlockDoesNotExistsException,
    CommitteeMemberDoesNotExistsException,
    GenesisBalanceDoesNotExistsException,
    InvalidAssetException,
    InvalidMemoKeyException,
    InvalidMessageSignature,
    InvalidWifError,
    KeyAlreadyInStoreException,
    KeyNotFound,
    MissingKeyError,
    NoWalletException,
    OfflineHasNoRPCException,
    ProposalDoesNotExistException,
    VestingBalanceDoesNotExistsException,
    WalletExists,
    WalletLocked,
    WitnessDoesNotExistsException,
    WorkerDoesNotExistsException,
    WrongMemoKey,
)


class RPCConnectionRequired(Exception):
    """An RPC connection is required."""


class AccountExistsException(Exception):
    """The requested account already exists."""


class ObjectNotInProposalBuffer(Exception):
    """Object was not found in proposal."""


class HtlcDoesNotExistException(Exception):
    """HTLC object does not exist."""
