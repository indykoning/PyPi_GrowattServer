"""Tests for growattServer.exceptions."""

from growattServer.exceptions import GrowattV1ApiError, GrowattV1ApiErrorCode


def test_growatt_v1_api_error_str_includes_code_and_msg():
    """str(exc) must surface error_code/error_msg, not just the generic message.

    Regression test for #154: GrowattV1ApiError used to pass only the generic
    message to super().__init__(), so error_code/error_msg never reached
    str(exc) — which is all that downstream consumers like Home Assistant's
    growatt_server integration log (`f"Growatt API error: {e}"`).

    Uses synthetic code/message values on purpose: which numeric code means
    what varies by endpoint (some codes are documented per-endpoint with a
    different meaning than the generic table in GrowattV1ApiErrorCode), so
    this test doesn't assert any particular real-world (operation, code)
    pairing — only that whatever values are passed in come through str(exc).
    """
    # error_code is an IntEnum here (as process_response often passes), not a
    # plain int — the f-string must format it as the numeric value, not the
    # enum's "GrowattV1ApiErrorCode.NO_PRIVILEGE" repr.
    exc = GrowattV1ApiError(
        "Error during test operation",
        error_code=GrowattV1ApiErrorCode.NO_PRIVILEGE,
        error_msg="some error detail",
    )

    assert str(exc) == "Error during test operation: [10011] some error detail"
    assert exc.error_code == GrowattV1ApiErrorCode.NO_PRIVILEGE
    assert exc.error_msg == "some error detail"
