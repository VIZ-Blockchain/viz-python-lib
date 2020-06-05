import pytest

from viz.blockchain import Blockchain


@pytest.fixture()
def blockchain(viz):
    return Blockchain(mode='head')


def test_stream_virtual_ops(blockchain):
    stream = blockchain.stream(start_block=1, end_block=2, filter_by='witness_reward')
    for op in stream:
        assert op['type'] == 'witness_reward'
        assert 'shares' in op


def test_stream_virtual_ops_raw_output(blockchain):
    stream = blockchain.stream(start_block=1, end_block=2, filter_by='witness_reward', raw_output=True)
    for op in stream:
        print(op)
        assert 'block' in op
        assert op['op'][0] == 'witness_reward'


def test_stream_real_ops(blockchain, viz, default_account):
    current = blockchain.get_current_block_num()
    viz.transfer('alice', 1, "VIZ", memo="test stream", account=default_account)
    ops = list(blockchain.stream(start_block=current, end_block=current + 3, filter_by='transfer'))
    assert ops[0]['from'] == default_account
    assert ops[0]['memo'] == 'test stream'

    ops = list(blockchain.stream(start_block=current + 3, end_block=current))
    assert ops
