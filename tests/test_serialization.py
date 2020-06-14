from binascii import hexlify

import pytest

from vizbase import operations
from vizbase.signedtransactions import Signed_Transaction

ref_block_num = 54051
ref_block_prefix = "2406554386"
expiration = "2020-06-02T13:38:03"


@pytest.fixture()
def _fixtures_plug(viz, default_account, request):
    request.cls.viz = viz
    request.cls.default_account = default_account


@pytest.mark.usefixtures("_fixtures_plug")
class TestSerialization:
    def get_hex(self, trx):
        """Get transaction hex."""
        try:
            trx.data.pop("signatures")
        except (AttributeError, KeyError, TypeError):
            pass
        return hexlify(bytes(trx)).decode("ascii")

    def do_test(self, op):
        tx = Signed_Transaction(
            ref_block_num=ref_block_num, ref_block_prefix=ref_block_prefix, expiration=expiration, operations=[op]
        )

        # strip last two zeroes, dunno where they come from
        node_hex = self.viz.rpc.get_transaction_hex(tx.json())[:-2]  # type: ignore
        local_hex = self.get_hex(tx)
        assert local_hex == node_hex

    def print_serialization(self, op):
        """Use this method to debug failed serialization."""
        for key, value in op.data.items():
            if isinstance(value, operations.GrapheneObject):
                self.print_serialization(value)
            else:
                print("{}: {}".format(key, self.get_hex(value)))

    def test_transfer(self):
        op = operations.Transfer(**{"from": "vvk", "to": "vvk2", "amount": "1.000 VIZ", "memo": "foo"})

        self.do_test(op)

    def test_versioned_chain_properties_update(self):
        props = {
            'account_creation_fee': '1.000 VIZ',
            'maximum_block_size': 65536,
            'create_account_delegation_ratio': 2,
            'create_account_delegation_time': 3600,
            'min_delegation': '10.000 VIZ',
            'min_curation_percent': 1000,
            'max_curation_percent': 2000,
            'bandwidth_reserve_percent': 1000,
            'bandwidth_reserve_below': '10.000 SHARES',
            'flag_energy_additional_cost': 1000,
            'vote_accounting_min_rshares': 100000,
            'committee_request_approve_min_percent': 1000,
            'inflation_witness_percent': 1000,
            'inflation_ratio_committee_vs_reward_fund': 5000,
            'inflation_recalc_period': 3600,
            'data_operations_cost_additional_bandwidth': 0,
            'witness_miss_penalty_percent': 1000,
            'witness_miss_penalty_duration': 3600,
            'create_invite_min_balance': '1.000 VIZ',
            'committee_create_request_fee': '1.000 VIZ',
            'create_paid_subscription_fee': '1.000 VIZ',
            'account_on_sale_fee': '1.000 VIZ',
            'subaccount_on_sale_fee': '1.000 VIZ',
            'witness_declaration_fee': '1.000 VIZ',
            'withdraw_intervals': 10,
        }
        data = {'owner': self.default_account, 'props': props}  # type: ignore
        op = operations.Versioned_chain_properties_update(**data)
        self.do_test(op)
