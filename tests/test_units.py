import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from worker.clean import reject_reason  # noqa: E402


def rec(text, raw):
    return {"id": "C1", "text": text, "teacher_raw": raw}


def test_valid_record_is_kept():
    raw = json.dumps({"intent": "weather_query", "date": None, "time": None, "place": "london"})
    assert reject_reason(rec("what is the weather in london", raw)) is None


def test_invalid_json_rejected_a():
    assert reject_reason(rec("hello", "not json")) == "a"


def test_wrong_keys_rejected_b():
    raw = json.dumps({"intent": "alarm_set", "date": None})
    assert reject_reason(rec("hello", raw)) == "b"


def test_bad_intent_rejected_c():
    raw = json.dumps({"intent": "play_music", "date": None, "time": None, "place": None})
    assert reject_reason(rec("hello", raw)) == "c"


def test_slot_not_in_command_rejected_d():
    raw = json.dumps({"intent": "alarm_set", "date": "friday", "time": None, "place": None})
    assert reject_reason(rec("set an alarm for sunday", raw)) == "d"
