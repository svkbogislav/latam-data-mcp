"""Live integration tests against the real upstream APIs.

Run with: pytest -m live
Skipped by default so the core suite stays offline-safe.
"""

import pytest
from fastmcp import Client

from server import mcp

pytestmark = [pytest.mark.live, pytest.mark.asyncio]


async def call(name: str, args: dict) -> dict:
    async with Client(mcp) as client:
        return (await client.call_tool(name, args)).data


async def test_chile_indicators_live():
    data = await call("chile_indicators", {"codes": ["UF", "USD", "UTM"]})
    assert data["indicators"]["UF"]["value_clp"] > 10_000
    assert data["indicators"]["USD"]["value_clp"] > 100


async def test_argentina_rates_live():
    data = await call("argentina_exchange_rates", {})
    assert data["usd_blue"]["sell"] > 0
    assert data["usd_official"]["sell"] > 0


async def test_brazil_rates_live():
    data = await call("brazil_market_rates", {})
    names = {r["name"].upper() for r in data["rates"]}
    assert {"SELIC", "CDI", "IPCA"} <= names


async def test_brazil_company_live():
    data = await call("brazil_company_lookup", {"cnpj": "00.000.000/0001-91"})
    assert "BANCO DO BRASIL" in data["legal_name"].upper()
    assert data["address"]["state"]


async def test_colombia_trm_live():
    data = await call("colombia_official_trm", {})
    assert data["usd_cop"] > 1000


async def test_latam_fx_live():
    data = await call("latam_exchange_rates", {})
    assert {"CLP", "ARS", "BRL", "MXN", "COP", "PEN", "UYU", "VES"} <= data["rates"].keys()


async def test_holidays_live():
    data = await call("public_holidays", {"country": "CL", "year": 2026})
    assert data["count"] >= 12
    dates = {h["date"] for h in data["holidays"]}
    assert "2026-09-18" in dates  # Fiestas Patrias


async def test_long_weekends_live():
    data = await call("long_weekends", {"country": "CL", "year": 2026})
    assert len(data["long_weekends"]) >= 3


async def test_next_holidays_live():
    data = await call("next_holidays", {"country": "MX"})
    assert len(data["upcoming"]) >= 1


async def test_brazil_bank_lookup_live():
    data = await call("brazil_bank_lookup", {"code": "1"})
    assert "BANCO DO BRASIL" in (data.get("full_name") or "").upper()
    missing = await call("brazil_bank_lookup", {"code": "99999"})
    assert "error" in missing


async def test_costa_rica_company_live():
    data = await call("costa_rica_company_lookup", {"cedula": "3101002346"})
    assert data.get("name")
    assert "delinquent" in data["status"]


async def test_costa_rica_fx_live():
    data = await call("costa_rica_exchange_rate", {})
    assert data["usd_crc"]["sell"] > 100


async def test_currency_convert_live():
    data = await call("currency_convert", {"amount": 100, "from_currency": "USD", "to_currency": "CLP"})
    assert data["converted"] > 1000  # 100 USD is many thousand CLP
    bad = await call("currency_convert", {"amount": 1, "from_currency": "USD", "to_currency": "ZZZ"})
    assert "error" in bad


async def test_business_days_live():
    # January 2026 in Chile: 31 days, 22 weekdays, Jan 1 (Thu) is a holiday -> 21
    data = await call("business_days",
                      {"country": "CL", "start_date": "2026-01-01", "end_date": "2026-01-31"})
    assert data["business_days"] == 21
    assert data["holidays_in_range"][0]["date"] == "2026-01-01"
