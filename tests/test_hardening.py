"""Regression tests for defects found in adversarial verification (v0.2 hardening)."""

import asyncio

import pytest
from fastmcp import Client

from latam_data.validators import VALIDATORS
from server import mcp


def check(country: str, tax_id: str) -> dict:
    return VALIDATORS[country][1](tax_id)


# --- Degenerate all-zero IDs must be rejected everywhere --------------------

ZERO_IDS = [
    ("CL", "00.000.000-0"), ("AR", "00000000000"), ("CO", "00000000"),
    ("PY", "0-0"), ("PY", "00"), ("GT", "00"), ("GT", "000000000000"),
    ("DO", "000000002"), ("VE", "V000000007"),
]


@pytest.mark.parametrize("country,tax_id", ZERO_IDS)
def test_all_zero_ids_rejected(country, tax_id):
    assert not check(country, tax_id)["valid"], f"{country} {tax_id} must be invalid"


# --- Unicode / hostile input must never crash, never validate ---------------

HOSTILE = [
    "012²456789", "1²3", "٢٠٠٥٥٣٦١٦٨٢", "GODE５６１２３１GR8",
    "８００１９７２６８４", "V５６８７２０３２2", "①②③④⑤⑥⑦⑧⑨",
    "", "   ", "K", "0-0", "\t\n", "𝟙𝟚𝟛", "12 345 678-5",
]


@pytest.mark.parametrize("code", list(VALIDATORS))
@pytest.mark.parametrize("bad", HOSTILE)
def test_no_crash_and_no_false_positive_on_unicode(code, bad):
    result = VALIDATORS[code][1](bad)  # must not raise
    if result["valid"]:
        # Anything accepted must round-trip to pure ASCII in its formatted form.
        assert result["formatted"].isascii(), f"{code} accepted non-ASCII {bad!r}"


# --- Argentina prefix validation --------------------------------------------

def test_ar_rejects_non_afip_prefixes():
    assert not check("AR", "06420636995")["valid"]
    assert not check("AR", "99000000007")["valid"]


def test_ar_valid_prefixes_still_pass():
    assert check("AR", "30-50001091-2")["valid"]
    assert check("AR", "20-12345678-6")["valid"]


def test_ar_remainder_10_maps_to_check_digit_9():
    # AFIP convention (matches python-stdnum): verificador 10 -> check digit 9
    assert check("AR", "20000000019")["valid"]


# --- Ecuador natural-person RUC with third digit 6 --------------------------

def test_ec_natural_person_ruc_third_digit_6():
    result = check("EC", "0261618151001")
    assert result["valid"], result.get("reason")
    assert result["type"] == "natural person"


# --- Colombia short NIT floor -----------------------------------------------

def test_co_rejects_short_nits():
    assert not check("CO", "098583")["valid"]   # 6 digits
    assert not check("CO", "9989458")["valid"]  # 7 digits


# --- Mexico honesty flag ----------------------------------------------------

def test_mx_flags_unverified_check_digit():
    result = check("MX", "GODE561231GR8")
    assert result["valid"]
    assert result["check_digit_verified"] is False


# --- business_days must not overflow on date.max ----------------------------

@pytest.mark.asyncio
async def test_business_days_no_overflow_and_year_guard():
    async with Client(mcp) as client:
        out = await client.call_tool(
            "business_days",
            {"country": "CL", "start_date": "9999-12-30", "end_date": "9999-12-31"})
    # 9999 is out of the supported year range -> structured error, no OverflowError
    assert "error" in out.data


@pytest.mark.asyncio
async def test_holiday_tools_reject_out_of_range_years():
    async with Client(mcp) as client:
        ph = await client.call_tool("public_holidays", {"country": "AR", "year": 1492})
        lw = await client.call_tool("long_weekends", {"country": "AR", "year": 1492})
    assert "out of the supported range" in ph.data["error"]
    assert "out of the supported range" in lw.data["error"]


# --- Empty-response contract: no raw TypeError leaks to the MCP layer -------

@pytest.mark.asyncio
async def test_empty_upstream_returns_structured_error(monkeypatch):
    from latam_data import apis

    async def fake_empty(url: str):
        raise apis.EmptyResponseError(url)

    monkeypatch.setattr(apis, "_get_json", fake_empty)
    async with Client(mcp) as client:
        for tool, args in [
            ("chile_indicators", {}), ("argentina_exchange_rates", {}),
            ("brazil_market_rates", {}), ("colombia_official_trm", {}),
            ("latam_exchange_rates", {}),
        ]:
            result = await client.call_tool(tool, args)
            assert "error" in result.data, f"{tool} leaked instead of returning error"
