from datetime import datetime, timedelta, timezone

import pytest

from viz.utils import json_expand, parse_time, time_diff, time_elapsed


def test_json_expand_parses_string_value():
    op = {"id": "proto", "json": '{"x": 1}'}
    result = json_expand(op)
    assert result["json"] == {"x": 1}


def test_json_expand_custom_key():
    op = {"json_metadata": '{"profile": {"name": "alice"}}'}
    result = json_expand(op, key_name="json_metadata")
    assert result["json_metadata"] == {"profile": {"name": "alice"}}


def test_json_expand_invalid_json_returns_empty_dict():
    op = {"json": "not-json"}
    result = json_expand(op)
    assert result["json"] == {}


def test_json_expand_missing_key_returns_input():
    op = {"other": "value"}
    assert json_expand(op) is op


def test_json_expand_empty_value_returns_input():
    op = {"json": ""}
    assert json_expand(op) is op


def test_json_expand_non_dict_input_returns_input():
    assert json_expand(["json", "x"]) == ["json", "x"]
    assert json_expand("string") == "string"
    assert json_expand(None) is None


def test_json_expand_dict_subclass():
    class MyDict(dict):
        pass

    op = MyDict({"json": '{"a": 2}'})
    result = json_expand(op)
    assert result["json"] == {"a": 2}


def test_parse_time_returns_naive_datetime():
    parsed = parse_time("2024-01-02T03:04:05")
    assert parsed == datetime(2024, 1, 2, 3, 4, 5)
    assert parsed.tzinfo is None


def test_time_diff_returns_timedelta():
    diff = time_diff("2024-01-02T00:00:00", "2024-01-01T00:00:00")
    assert diff == timedelta(days=1)


def test_time_elapsed_with_string_input():
    past = (datetime.now(timezone.utc) - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%S")
    elapsed = time_elapsed(past)
    assert elapsed.total_seconds() >= 9


def test_time_elapsed_with_naive_datetime_treated_as_utc():
    past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=5)
    elapsed = time_elapsed(past)
    assert elapsed.total_seconds() >= 4


def test_time_elapsed_with_aware_datetime():
    past = datetime.now(timezone.utc) - timedelta(seconds=5)
    elapsed = time_elapsed(past)
    assert elapsed.total_seconds() >= 4


def test_time_elapsed_future_is_negative():
    future = datetime.now(timezone.utc) + timedelta(seconds=60)
    elapsed = time_elapsed(future)
    assert elapsed.total_seconds() < 0


@pytest.mark.parametrize("bad", ["2024/01/02", "not a date", ""])
def test_parse_time_rejects_invalid(bad):
    with pytest.raises(ValueError):
        parse_time(bad)
