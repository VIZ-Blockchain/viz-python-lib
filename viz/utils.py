# -*- coding: utf-8 -*-
import json
from datetime import datetime

from toolz import assoc, update_in


def json_expand(json_op, key_name="json"):
    """Convert a string json object to Python dict in an op."""
    if type(json_op) == dict and key_name in json_op and json_op[key_name]:
        try:
            return update_in(json_op, [key_name], json.loads)
        except json.JSONDecodeError:
            return assoc(json_op, key_name, {})

    return json_op


def time_elapsed(event_time):
    """Takes a string time from blockchain event, and returns a time delta from now."""
    if isinstance(event_time, str):
        event_time = parse_time(event_time)
    return datetime.utcnow() - event_time


def parse_time(event_time):
    """Take a string representation of time from the blockchain, and parse it into datetime object."""
    return datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S')


def time_diff(time1, time2):
    return parse_time(time1) - parse_time(time2)
