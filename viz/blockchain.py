# -*- coding: utf-8 -*-
import hashlib
import json
import time
from typing import Iterator, List, Optional, Union

from graphenecommon.blockchain import Blockchain as GrapheneBlockchain

from vizbase import operationids

from .block import Block
from .instance import BlockchainInstance


@BlockchainInstance.inject
class Blockchain(GrapheneBlockchain):
    """
    This class allows to access the blockchain and read data from it.

    :param viz.viz.Client blockchain_instance: Client
             instance
    :param str mode: Irreversible block (``irreversible``) or
        actual head block (``head``) (default: *irreversible*)
    :param int max_block_wait_repetition: maximum wait time for
        next block is ``max_block_wait_repetition * block_interval`` (default 3)

    This class let's you deal with blockchain related data and methods.
    """

    @staticmethod
    def hash_op(event: dict) -> str:
        """This method generates a hash of blockchain operation."""
        data = json.dumps(event, sort_keys=True)
        return hashlib.sha1(bytes(data, "utf-8")).hexdigest()  # noqa: DUO130

    def define_classes(self) -> None:
        self.block_class = Block
        self.operationids = operationids

    def get_block_interval(self) -> int:
        """Override class from graphenelib because our API is different."""
        return self.blockchain.rpc.config.get("CHAIN_BLOCK_INTERVAL")

    def stream_from(
        self,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        batch_operations: bool = False,
        full_blocks: bool = False,
        only_virtual_ops: bool = False,
    ) -> Iterator[dict]:
        """
        This call yields raw blocks or operations depending on ``full_blocks`` param.

        By default, this generator will yield operations, one by one.
        You can choose to yield lists of operations, batched to contain
        all operations for each block with ``batch_operations=True``.
        You can also yield full blocks instead, with ``full_blocks=True``.

        :param int start_block: Block to start with. If not provided, current (head) block is used.
        :param int end_block: Stop iterating at this block. If not provided, this generator will run forever
            (streaming mode).
        :param bool batch_operations: (Defaults to False) Rather than yielding operations one by one,
                yield a list of all operations for each block.
        :param bool full_blocks: (Defaults to False) Rather than yielding operations, return raw, unedited blocks as
                provided by blokchain_instance. This mode will NOT include virtual operations.
        :param bool only_virtual_ops: stream only virtual operations
        """

        # Let's find out how often blocks are generated!
        block_interval = self.get_block_interval()

        if start_block is None:
            start_block = self.get_current_block_num()

        is_reversed = end_block and start_block > end_block

        while True:
            head_block = self.get_current_block_num()

            range_params = (start_block, head_block + 1, 1)
            if is_reversed:
                range_params = (start_block, max(0, end_block - 2), -1)  # type: ignore

            for block_num in range(*range_params):  # type: ignore
                if end_block is not None:
                    if is_reversed and block_num < end_block:
                        return
                    elif not is_reversed and block_num > end_block:
                        return

                if full_blocks:
                    block = self.blockchain.rpc.get_block(block_num)
                    # inject block number
                    block.update({"block_num": block_num})
                    yield block
                elif batch_operations:
                    yield self.blockchain.rpc.get_ops_in_block(block_num, only_virtual_ops)
                else:
                    ops = self.blockchain.rpc.get_ops_in_block(block_num, only_virtual_ops)
                    for op in ops:
                        # avoid yielding empty ops
                        if op:
                            yield op

            # next round
            start_block = head_block + 1
            time.sleep(block_interval)

    def stream(
        self,
        filter_by: Optional[Union[str, List[str]]] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        raw_output: bool = False,
    ) -> Iterator[dict]:
        """
        Yield a stream of specific operations, starting with current head block.

        This method can work in 2 modes:
        1. Whether only real operations are requested, it will use get_block() API call, so you don't need to have
        neigher operation_history nor accunt_history plugins enabled.
        2. Whether you're requesting any of the virtual operations, your node should have operation_history or
        accunt_history plugins enabled and appropriate settings for the history-related params should be set
        (history-start-block, history-whitelist-ops or history-blacklist-ops).

        The dict output is formated such that ``type`` caries the operation type, timestamp and block_num are taken
        from the block the operation was stored in and the other key depend on the actual operation.

        :param str,list filter_by: List of operations to filter for
        :param int start_block: Block to start with. If not provided, current (head) block is used.
        :param int end_block: Stop iterating at this block. If not provided, this generator will run forever
            (streaming mode).
        :param bool raw_output: when streaming virtual ops, yield raw ops instead of extended ops format

        Example op when streaming virtual ops, ``raw_output = False``:

        .. code-block:: python

            {
                '_id': 'e2fabb498706edfccd1114921f05d95e8fd64e4c',
                'type': 'witness_reward',
                'timestamp': '2020-05-29T19:07:48',
                'block_num': 1,
                'trx_id': '0000000000000000000000000000000000000000',
                'witness': 'committee',
                'shares': '0.032999 SHARES',
            }

        Virtual op with ``raw_output = True``:

        .. code-block:: python

            {
                'trx_id': '0000000000000000000000000000000000000000',
                'block': 1,
                'trx_in_block': 65535,
                'op_in_trx': 0,
                'virtual_op': 1,
                'timestamp': '2020-05-29T19:28:08',
                'op': ['witness_reward', {'witness': 'committee', 'shares': '0.032999 SHARES'}],
            }


        Real op example:

        .. code-block:: python

            {
                'type': 'transfer',
                'timestamp': '2020-05-29T19:20:07',
                'block_num': 6,
                'from': 'viz',
                'to': 'alice',
                'amount': '1.000 VIZ',
                'memo': 'test stream',
            }
        """
        if filter_by is None:
            filter_by = []

        if isinstance(filter_by, str):
            filter_by = [filter_by]

        if not bool(set(filter_by).intersection(operationids.VIRTUAL_OPS)):
            # uses get_block instead of get_ops_in_block
            for block in self.stream_from(full_blocks=True, start_block=start_block, end_block=end_block):
                for tx in block["transactions"]:
                    for op in tx["operations"]:
                        if not filter_by or op[0] in filter_by:
                            operation = {
                                "type": op[0],
                                "timestamp": block.get("timestamp"),
                                "block_num": block.get("block_num"),
                            }
                            operation.update(op[1])
                            yield operation
        else:
            # uses get_ops_in_block
            only_virtual_ops = not bool(set(filter_by).difference(operationids.VIRTUAL_OPS))
            for op in self.stream_from(
                full_blocks=False, only_virtual_ops=only_virtual_ops, start_block=start_block, end_block=end_block
            ):

                if not filter_by or op["op"][0] in filter_by:
                    if raw_output:
                        yield op
                    else:
                        operation = {
                            "_id": self.hash_op(op),
                            "type": op["op"][0],
                            "timestamp": op.get("timestamp"),
                            "block_num": op.get("block"),
                            "trx_id": op.get("trx_id"),
                        }
                        operation.update(op["op"][1])
                        yield operation
