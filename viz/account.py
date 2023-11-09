from typing import TYPE_CHECKING, Generator, List, Optional, Union
from warnings import warn
from graphenecommon.exceptions import AccountDoesNotExistsException
from toolz import dissoc

from .amount import Amount
from .blockchain import Blockchain
from .instance import shared_blockchain_instance
from .utils import json_expand, parse_time, time_elapsed

if TYPE_CHECKING:
    from .viz import Client  # noqa: F401

HistoryGenerator = Generator[Union[dict, list], None, int]


class Account(dict):
    """
    This class allows to easily access Account data.

    :param str account_name: Name of the account
    :param viz.viz.Client blockchain_instance: Client
             instance
    """

    def __init__(self, account_name: str, blockchain_instance: Optional['Client'] = None) -> None:
        self.blockchain_instance = blockchain_instance or shared_blockchain_instance()
        self.name = account_name

        self.refresh()

    @property
    def balances(self):
        """Shortcut to :py:func:`get_balances`"""
        return self.get_balances()

    @property
    def energy(self):
        """Account energy at the moment of last use (stale)"""
        cfg = self.blockchain_instance.rpc.config
        return self['energy'] / cfg['CHAIN_1_PERCENT']

    def refresh(self):
        """Loads account object from blockchain."""
        try:
            account = self.blockchain_instance.rpc.get_accounts([self.name])[0]
        except IndexError:
            raise AccountDoesNotExistsException

        # load json_metadata
        account = json_expand(account, "json_metadata")
        super(Account, self).__init__(account)

    def get_balances(self) -> dict:
        """
        Obtain account balances.

        :return: dict with balances like ``{'VIZ': 49400000.0, 'SHARES': 0.0}``
        """
        balance = Amount(self["balance"])
        vesting = Amount(self["vesting_shares"])

        return {balance.symbol: balance.amount, vesting.symbol: vesting.amount}

    def current_energy(self) -> float:
        """Returns current account energy (actual data, counts regenerated energy)"""
        self.refresh()
        last_vote_time = parse_time(self['last_vote_time'])
        elapsed_time = time_elapsed(last_vote_time)
        cfg = self.blockchain_instance.rpc.config
        regenerated_energy = (
            cfg['CHAIN_100_PERCENT'] * elapsed_time.total_seconds() / cfg['CHAIN_ENERGY_REGENERATION_SECONDS']
        )
        current_energy = self['energy'] + regenerated_energy
        energy = min(current_energy, cfg['CHAIN_100_PERCENT']) / cfg['CHAIN_1_PERCENT']

        return energy

    def virtual_op_count(self) -> int:
        """Returns number of virtual ops performed by this account."""
        try:
            last_item = self.blockchain_instance.rpc.get_account_history(self.name, -1, 0)[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def get_withdraw_routes(self, type_: str = 'all') -> dict:
        """
        Get vesting withdraw routes.

        :param type_: route type, one of `all`, `incoming`, `outgoing`
        :return: list with routes

        Example return:

        .. code-block:: python

            [
                {
                    'from_account': 'alice',
                    'to_account': 'bob',
                    'percent': 10000,
                    'auto_vest': False
                }
            ]
        """
        return self.blockchain_instance.rpc.get_withdraw_routes(self.name, type_)

    def get_account_history(
        self,
        index: int,
        limit: int,
        start: Optional[int] = None,
        stop: Optional[int] = None,
        order: int = -1,
        filter_by: Optional[Union[str, List[str]]] = None,
        raw_output: bool = False,
    ) -> HistoryGenerator:
        """
        A generator over get_account_history RPC.

        It offers serialization, filtering and fine grained iteration control.

        .. note::

            This method is mostly for internal use, probably you need :py:func:`history`.

        :param int index: start index for get_account_history
        :param int limit: How many items in account history will be scanned (any ops, not only filtered)
        :param int start: (Optional) skip items until this index
        :param int stop: (Optional) stop iteration early at this index
        :param order: (1, -1): 1 for chronological, -1 for reverse order
        :param str,list filter_by: filter out all but these operations
        :param bool raw_output: (Defaults to False). If True, return history in
            steemd format (unchanged).
        """
        if isinstance(filter_by, str):
            filter_by = [filter_by]

        op_count = 0

        history = self.blockchain_instance.rpc.get_account_history(self.name, index, limit)
        for item in history[::order]:
            index, event = item

            # start and stop utilities for chronological generator
            if start and index < start:
                continue

            if stop and index > stop:
                return op_count

            op_type, op = event["op"]
            # removes specified key from dict
            block_props = dissoc(event, "op")

            def construct_op(account_name):
                # verbatim output from steemd
                if raw_output:
                    return item

                # index can change during reindexing in
                # future hard-forks. Thus we cannot take it for granted.
                immutable = op.copy()
                immutable.update(block_props)
                immutable.update({"account": account_name, "type": op_type})
                _id = Blockchain.hash_op(immutable)
                immutable.update({"_id": _id, "index": index})
                return immutable

            if filter_by is None or op_type in filter_by:
                yield construct_op(self.name)
                op_count += 1

        return op_count

    def history(
        self,
        filter_by: Optional[Union[str, List[str]]] = None,
        start: int = 0,
        batch_size: int = 1000,
        raw_output: bool = False,
        limit: int = -1,
    ) -> HistoryGenerator:
        """
        THIS FUNCTION IS DEPRECATED. PLEASE USE :py:func:`history_reverse` INSTEAD.

        Stream account history in chronological order. 

        This generator yields history items which may be in list or dict form depending on ``raw_output``.
        Output is similar to :py:func:`history_reverse`.

        :param str,list filter_by: filter out all but these operations
        :param int start: (Optional) skip items until this index
        :param int batch_size: (Optional) request as many items from API in each chunk
        :param bool raw_output: (Defaults to False). If True, return history in
            steemd format (unchanged).
        :param int limit: (Optional) limit number of filtered items to this amount (-1 means unlimited).
            This is a rough limit, actual results could be a bit longer
        :return: number of ops
        """
        warn("Function `history` is not recommened. Use `history_reverse` instead.", DeprecationWarning, stacklevel=2)

        op_count = 0

        max_index = self.virtual_op_count()
        if not max_index:
            return op_count

        start_index = start + batch_size
        i = start_index
        while i < max_index + batch_size:
            count = yield from self.get_account_history(
                index=i,
                limit=batch_size,
                start=i - batch_size,
                stop=max_index,
                order=1,
                filter_by=filter_by,
                raw_output=raw_output,
            )
            i += batch_size + 1
            op_count += count

            if limit > 0 and op_count >= limit:
                break

        return op_count

    def history_reverse(
        self,
        filter_by: Optional[Union[str, List[str]]] = None,
        batch_size: int = 1000,
        raw_output: bool = False,
        limit: int = -1,
    ) -> HistoryGenerator:
        """
        Stream account history in reverse chronological order.

        This generator yields history items which may be in list or dict form depending on ``raw_output``.

        :param str,list filter_by: filter out all but these operations
        :param int batch_size: (Optional) request as many items from API in each chunk
        :param bool raw_output: (Defaults to False). If True, return history in
            steemd format (unchanged).
        :param int limit: (Optional) limit number of filtered items to this amount (-1 means unlimited).
            This is a rough limit, actual results could be a bit longer
        :return: number of ops

        Non-raw output example of yielded item:

        .. code-block:: python

            {
                'from': 'viz',
                'to': 'null',
                'amount': '1.000 VIZ',
                'memo': 'test',
                'trx_id': '592010ade718c91a81cba3b8378c35ed81d23f23',
                'block': 5,
                'trx_in_block': 0,
                'op_in_trx': 0,
                'virtual_op': 0,
                'timestamp': '2020-05-19T08:10:47',
                'account': 'viz',
                'type': 'transfer',
                '_id': 'd1ed77ae861bb1ecc26a82dd275cc80e5ac124a6',
                'index': 0,
            }

        Raw output example of single item:

        .. code-block:: python

            [
                0,
                {
                    'trx_id': '592010ade718c91a81cba3b8378c35ed81d23f23',
                    'block': 5,
                    'trx_in_block': 0,
                    'op_in_trx': 0,
                    'virtual_op': 0,
                    'timestamp': '2020-05-19T08:10:47',
                    'op': ['transfer', {'from': 'viz', 'to': 'null', 'amount': '1.000 VIZ', 'memo': 'test'}],
                },
            ]
        """
        op_count = 0

        start_index = self.virtual_op_count()
        if not start_index:
            return op_count

        i = start_index
        while i > 0:
            if i - batch_size < 0:
                batch_size = i
            count = yield from self.get_account_history(
                index=i, limit=batch_size, order=-1, filter_by=filter_by, raw_output=raw_output,
            )
            i -= batch_size + 1
            op_count += count

            if limit > 0 and op_count >= limit:
                break

        return op_count
