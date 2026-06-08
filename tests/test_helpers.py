"""Tests for pure helper functions (no HTTP mocking needed)."""

from __future__ import annotations

import datetime

import pytest

from growattServer import Timespan, hash_password


class TestHashPassword:
    def test_known_value(self):
        result = hash_password("test")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_c_substitution(self):
        """Bytes with a leading '0' nibble get replaced with 'c'."""
        result = hash_password("test")
        # Verify no '0' appears at even positions (the algorithm replaces them)
        for i in range(0, len(result), 2):
            assert result[i] != "0"

    def test_empty_string(self):
        result = hash_password("")
        assert isinstance(result, str)
        assert len(result) == 32

    def test_deterministic(self):
        assert hash_password("hello") == hash_password("hello")

    def test_different_inputs(self):
        assert hash_password("a") != hash_password("b")


class TestTimespan:
    def test_values(self):
        assert Timespan.hour == 0
        assert Timespan.day == 1
        assert Timespan.month == 2

    def test_is_int(self):
        assert isinstance(Timespan.hour, int)


class TestGetDateString:
    """Test _get_date_string via a GrowattApi instance."""

    def test_day_format(self):
        from growattServer import GrowattApi
        api = GrowattApi.__new__(GrowattApi)
        dt = datetime.datetime(2024, 3, 15, tzinfo=datetime.UTC)
        assert api._get_date_string(Timespan.day, dt) == "2024-03-15"

    def test_hour_format(self):
        from growattServer import GrowattApi
        api = GrowattApi.__new__(GrowattApi)
        dt = datetime.datetime(2024, 3, 15, tzinfo=datetime.UTC)
        assert api._get_date_string(Timespan.hour, dt) == "2024-03-15"

    def test_month_format(self):
        from growattServer import GrowattApi
        api = GrowattApi.__new__(GrowattApi)
        dt = datetime.datetime(2024, 3, 15, tzinfo=datetime.UTC)
        assert api._get_date_string(Timespan.month, dt) == "2024-03"

    def test_default_date_uses_now(self):
        from growattServer import GrowattApi
        api = GrowattApi.__new__(GrowattApi)
        result = api._get_date_string(Timespan.day)
        today = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
        assert result == today

    def test_invalid_timespan_raises(self):
        from growattServer import GrowattApi
        api = GrowattApi.__new__(GrowattApi)
        with pytest.raises(ValueError, match="Timespan"):
            api._get_date_string("invalid")
