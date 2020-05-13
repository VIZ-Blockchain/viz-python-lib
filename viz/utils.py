# -*- coding: utf-8 -*-
import json

# Load methods from graphene and provide them to viz
from graphenecommon.utils import (
    assets_from_string,
    formatTime,
    formatTimeFromNow,
    formatTimeString,
    parse_time,
    timeFormat,
)
from toolz import assoc, update_in


def json_expand(json_op, key_name="json"):
    """Convert a string json object to Python dict in an op."""
    if type(json_op) == dict and key_name in json_op and json_op[key_name]:
        try:
            return update_in(json_op, [key_name], json.loads)
        except JSONDecodeError:
            return assoc(json_op, key_name, {})

    return json_op
