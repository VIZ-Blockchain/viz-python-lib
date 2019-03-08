import datetime
import math
import time

from contextlib import suppress
from toolz import dissoc
from funcy import get_in

from .amount import Amount
from .blockchain import Blockchain
from .converter import Converter
from .instance import shared_blockchain_instance
from .utils import parse_time, json_expand
from .exceptions import AccountDoesNotExistsException


class Account(dict):
    """ This class allows to easily access Account data

        :param str account_name: Name of the account
        :param viz.viz.Client blockchain_instance: Client
                 instance
    """

    def __init__(self, account_name, blockchain_instance=None):
        self.blockchain_instance = blockchain_instance or shared_blockchain_instance()
        self.name = account_name

        # caches
        self._converter = None

        self.refresh()

    def _get_account(self, name, **kwargs):
        """ Get full account details from account name

            :param str name: Account name
        """
        return self.blockchain_instance.rpc.get_accounts([name])[0]

    def refresh(self):
        account = self._get_account(self.name)
        if not account:
            raise AccountDoesNotExistsException

        # load json_metadata
        account = json_expand(account, "json_metadata")
        super(Account, self).__init__(account)

    def __getitem__(self, key):
        return super(Account, self).__getitem__(key)

    def items(self):
        return super(Account, self).items()

    @property
    def converter(self):
        if not self._converter:
            self._converter = Converter(blockchain_instance=self.blockchain_instance)
        return self._converter

    @property
    def profile(self):
        with suppress(TypeError):
            return get_in(self, ["json_metadata", "profile"], default={})

    @property
    def shares_as_core(self):
        shares = Amount(self["vesting_shares"]).amount
        # TODO: round or use Decimal in Converter
        return self.converter.shares_to_core(shares)

    @property
    def balances(self):
        return self.get_balances()

    def get_balances(self):
        balance = Amount(self["balance"])
        vesting = Amount(self["vesting_shares"])
        return {balance.symbol: balance.amount, vesting.symbol: vesting.amount}

    def energy(self):
        return self["energy"] / 100

    def get_followers(self, limit: int = None, offset: str = None):
        # TODO: is this needed?
        return [
            x["follower"]
            for x in self._get_followers(
                direction="follower", limit=limit, offset=offset
            )
        ]

    def get_following(self, limit: int = None, offset: str = None):
        # TODO: is this needed?
        return [
            x["following"]
            for x in self._get_followers(
                direction="following", limit=limit, offset=offset
            )
        ]

    def _get_followers(self, direction="follower", limit=None, offset=""):
        # TODO: is this needed?
        users = []

        get_users = {
            "follower": self.blockchain_instance.get_followers,
            "following": self.blockchain_instance.get_following,
        }[direction]

        limit = limit or 10 ** 6
        max_request_limit = 100
        left_number = limit

        while left_number > 0:
            select_limit = min(left_number, max_request_limit)
            result = get_users(self.name, offset, "blog", select_limit)
            users.extend(result)

            has_next = len(users) < limit and len(result) >= select_limit
            if has_next:
                if users:
                    del users[-1]
                offset = result[-1][direction]

                left_number = left_number - len(result) + 1
            else:
                left_number = 0

        return users

    def virtual_op_count(self):
        try:
            last_item = self.blockchain_instance.rpc.get_account_history(
                self.name, -1, 0
            )[0][0]
        except IndexError:
            return 0
        else:
            return last_item

    def get_withdraw_routes(self):
        return self.blockchain_instance.rpc.get_withdraw_routes(self.name, "all")

    @staticmethod
    def filter_by_date(items, start_time, end_time=None):
        start_time = parse_time(start_time).timestamp()
        if end_time:
            end_time = parse_time(end_time).timestamp()
        else:
            end_time = time.time()

        filtered_items = []
        for item in items:
            item_time = None
            if "time" in item:
                item_time = item["time"]
            elif "timestamp" in item:
                item_time = item["timestamp"]

            if item_time:
                timestamp = parse_time(item_time).timestamp()
                if end_time > timestamp > start_time:
                    filtered_items.append(item)

        return filtered_items

    def get_account_history(
        self,
        index,
        limit,
        start=None,
        stop=None,
        order=-1,
        filter_by=None,
        raw_output=False,
    ):
        """ A generator over steemd.get_account_history.

        It offers serialization, filtering and fine grained iteration control.

        Args:
            index (int): start index for get_account_history
            limit (int): How many items in account history will be scanned (any ops, not only filtered)
            start (int): (Optional) skip items until this index
            stop (int): (Optional) stop iteration early at this index
            order: (1, -1): 1 for chronological, -1 for reverse order
            filter_by (str, list): filter out all but these operations
            raw_output (bool): (Defaults to False). If True, return history in
                steemd format (unchanged).
        """
        history = self.blockchain_instance.rpc.get_account_history(
            self.name, index, limit
        )
        for item in history[::order]:
            index, event = item

            # start and stop utilities for chronological generator
            if start and index < start:
                continue

            if stop and index > stop:
                return

            op_type, op = event["op"]
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

            if filter_by is None:
                yield construct_op(self.name)
            else:
                if type(filter_by) is list:
                    if op_type in filter_by:
                        yield construct_op(self.name)

                if type(filter_by) is str:
                    if op_type == filter_by:
                        yield construct_op(self.name)

    def history(self, filter_by=None, start=0, batch_size=1000, raw_output=False):
        """ Stream account history in chronological order.
        """
        max_index = self.virtual_op_count()
        if not max_index:
            return

        start_index = start + batch_size
        i = start_index
        while i < max_index + batch_size:
            yield from self.get_account_history(
                index=i,
                limit=batch_size,
                start=i - batch_size,
                stop=max_index,
                order=1,
                filter_by=filter_by,
                raw_output=raw_output,
            )
            i += batch_size + 1

    def history_reverse(self, filter_by=None, batch_size=1000, raw_output=False):
        """ Stream account history in reverse chronological order.
        """
        start_index = self.virtual_op_count()
        if not start_index:
            return

        i = start_index
        while i > 0:
            if i - batch_size < 0:
                batch_size = i
            yield from self.get_account_history(
                index=i,
                limit=batch_size,
                order=-1,
                filter_by=filter_by,
                raw_output=raw_output,
            )
            i -= batch_size + 1

    def rawhistory(self, first=99999999999, limit=-1, only_ops=[], exclude_ops=[]):
        """ Returns a generator for individual account transactions. The
            latest operation will be first. This call can be used in a
            ``for`` loop.

            :param str account: account name to get history for
            :param int first: sequence number of the first transaction to return
            :param int limit: limit number of filtered operations to return
            :param array only_ops: Limit generator by these operations
        """
        cnt = 0
        _limit = 100
        if _limit > first:
            _limit = first
        while first > 0:
            # RPC call
            txs = self.blockchain_instance.rpc.get_account_history(
                self.name, first, _limit
            )
            for i in txs[::-1]:
                if exclude_ops and i[1]["op"][0] in exclude_ops:
                    continue
                if not only_ops or i[1]["op"][0] in only_ops:
                    cnt += 1
                    yield i
                    if limit >= 0 and cnt >= limit:
                        break
            if limit >= 0 and cnt >= limit:
                break
            if len(txs) < _limit:
                break
            first = txs[0][0] - 1  # new first
            if _limit > first:
                _limit = first
