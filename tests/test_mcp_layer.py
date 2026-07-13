"""End-to-end tests through the MCP protocol layer (in-process client)."""

import pytest
from fastmcp import Client

from server import mcp

EXPECTED_TOOLS = {
    "validate_tax_id", "chile_indicators", "argentina_exchange_rates",
    "brazil_market_rates", "brazil_company_lookup", "colombia_official_trm",
    "latam_exchange_rates", "public_holidays", "next_holidays",
    "long_weekends", "business_days",
}


@pytest.mark.asyncio
async def test_all_tools_exposed():
    async with Client(mcp) as client:
        tools = {t.name for t in await client.list_tools()}
    assert tools == EXPECTED_TOOLS


@pytest.mark.asyncio
async def test_validate_through_protocol():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_tax_id", {"country": "cl", "tax_id": "60.910.000-1"})
    assert result.data["valid"] is True
    assert result.data["id_type"] == "RUT"


@pytest.mark.asyncio
async def test_unsupported_country_lists_supported():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "validate_tax_id", {"country": "XX", "tax_id": "123"})
    assert "unsupported" in result.data["error"]
    assert "CL" in result.data["supported"]


@pytest.mark.asyncio
async def test_business_days_input_validation():
    async with Client(mcp) as client:
        bad_date = await client.call_tool(
            "business_days",
            {"country": "CL", "start_date": "2026-13-01", "end_date": "2026-12-31"})
        swapped = await client.call_tool(
            "business_days",
            {"country": "CL", "start_date": "2026-02-01", "end_date": "2026-01-01"})
    assert "invalid date" in bad_date.data["error"]
    assert "before" in swapped.data["error"]
