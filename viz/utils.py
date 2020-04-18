# -*- coding: utf-8 -*-
import json

from toolz import update_in, assoc

from .exceptions import ObjectNotInProposalBuffer
from .instance import BlockchainInstance

# Load methods from graphene and provide them to viz
from graphenecommon.utils import (
    formatTime,
    timeFormat,
    formatTimeString,
    formatTimeFromNow,
    parse_time,
    assets_from_string,
)


def json_expand(json_op, key_name="json"):
    """ Convert a string json object to Python dict in an op. """
    if type(json_op) == dict and key_name in json_op and json_op[key_name]:
        try:
            return update_in(json_op, [key_name], json.loads)
        except JSONDecodeError:
            return assoc(json_op, key_name, {})

    return json_op
