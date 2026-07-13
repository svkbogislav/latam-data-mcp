"""LatAm Data MCP — Latin American data tools for AI agents.

Tax-ID validation for 12 countries, economic indicators, exchange
rates, company lookups, holidays and business-day math — the LatAm
data layer your agent is missing.
"""

from __future__ import annotations

import re
from datetime import date

import httpx
from fastmcp import FastMCP

from latam_data import apis
from latam_data.bank import BANK_VALIDATORS
from latam_data.validators import VALIDATORS

mcp = FastMCP(
    "LatAm Data",
    instructions=(
        "Latin American data toolkit. Validate national tax IDs for 12 countries "
        "(Chile, Argentina, Mexico, Brazil, Colombia, Peru, Uruguay, Ecuador, "
        "Paraguay, Venezuela, Guatemala, Dominican Republic), fetch Chilean "
        "indicators (UF/UTM/USD), Argentine blue-vs-official rates, Brazilian "
        "SELIC/CDI/IPCA and company data by CNPJ, Colombia's official TRM, "
        "region-wide FX, public holidays, long weekends, and business-day counts."
    ),
)


MIN_YEAR, MAX_YEAR = 1975, 2075


def _api_error(exc: Exception, source: str) -> dict:
    return {"error": f"upstream data source unavailable ({source})", "detail": str(exc)}


def _check_year(year: int) -> dict | None:
    if not MIN_YEAR <= year <= MAX_YEAR:
        return {"error": f"year {year} is out of the supported range ({MIN_YEAR}-{MAX_YEAR})"}
    return None


# ---------------------------------------------------------------------------
# Tax IDs
# ---------------------------------------------------------------------------

@mcp.tool
def validate_tax_id(country: str, tax_id: str) -> dict:
    """Validate a Latin American national tax ID, including its check digit.

    Supported countries (ISO 3166-1 alpha-2): CL (RUT), AR (CUIT/CUIL),
    MX (RFC), BR (CPF or CNPJ — auto-detected, including 2026 alphanumeric
    CNPJs), CO (NIT), PE (RUC), UY (RUT), EC (cédula or RUC — auto-detected),
    PY (RUC), VE (RIF), GT (NIT), DO (RNC).

    Verifies the country's check digit where one is algorithmically
    verifiable. Exception: Mexico's RFC — SAT-issued RFCs deviate from the
    published check-character algorithm, so for MX only the format and the
    embedded birth/incorporation date are validated (the result carries
    "check_digit_verified": false to make this explicit).

    Returns validity, canonical formatting, and — where the ID encodes it —
    whether it belongs to a person, company, or public entity.
    """
    code = country.strip().upper()
    if code not in VALIDATORS:
        return {"error": f"unsupported country '{country}'",
                "supported": {c: name for c, (name, _) in VALIDATORS.items()}}
    id_name, validator = VALIDATORS[code]
    result = validator(tax_id)
    return {"country": code, "id_type": result.pop("id_type", id_name),
            "input": tax_id, **result}


@mcp.tool
def validate_bank_account(country: str, account: str) -> dict:
    """Validate a Latin American bank account / interbank code, check digit included.

    Supported (ISO 3166-1 alpha-2): MX (CLABE, 18 digits), AR (CBU/CVU,
    22 digits — CVU covers virtual accounts like Mercado Pago).
    Returns validity, canonical formatting, and the decoded structure —
    bank code and name, branch, and account number. Essential for fintech,
    payouts, and payment-collection agents that must confirm an account is
    well-formed before initiating a transfer.
    """
    code = country.strip().upper()
    if code not in BANK_VALIDATORS:
        return {"error": f"unsupported country '{country}'",
                "supported": {c: name for c, (name, _) in BANK_VALIDATORS.items()}}
    id_name, validator = BANK_VALIDATORS[code]
    return {"country": code, "account_type": id_name, "input": account,
            **validator(account)}


# ---------------------------------------------------------------------------
# Chile
# ---------------------------------------------------------------------------

@mcp.tool
async def chile_indicators(codes: list[str] | None = None) -> dict:
    """Get current Chilean economic indicators and currency values in CLP.

    Includes UF (Unidad de Fomento), UTM (Unidad Tributaria Mensual),
    USD (observed dollar), EUR and other market-quoted currencies.
    Optionally filter with `codes`, e.g. ["UF", "USD"]. Values are CLP per unit.
    """
    try:
        rows = await apis.chile_indicators()
    except httpx.HTTPError as exc:
        return _api_error(exc, "gael.cloud")
    wanted = {c.strip().upper() for c in codes} if codes else None
    indicators = {r["code"]: {"name": r["name"], "value_clp": r["value_clp"]}
                  for r in rows if not wanted or r["code"] in wanted}
    out = {"currency": "CLP", "indicators": indicators}
    if wanted:
        missing = wanted - indicators.keys()
        if missing:
            out["not_found"] = sorted(missing)
    return out


# ---------------------------------------------------------------------------
# Argentina
# ---------------------------------------------------------------------------

@mcp.tool
async def argentina_exchange_rates() -> dict:
    """Get current Argentine peso (ARS) exchange rates: official vs "blue".

    The gap between the official and informal (blue) rate is essential
    context for any pricing, invoicing or purchasing decision in Argentina.
    """
    try:
        return {"currency": "ARS", **await apis.argentina_rates()}
    except httpx.HTTPError as exc:
        return _api_error(exc, "bluelytics")


# ---------------------------------------------------------------------------
# Brazil
# ---------------------------------------------------------------------------

@mcp.tool
async def brazil_market_rates() -> dict:
    """Get Brazil's key market rates: SELIC (policy rate), CDI, and IPCA (inflation).

    Annual percentage values, as published via BrasilAPI.
    """
    try:
        return {"rates": await apis.brazil_rates()}
    except httpx.HTTPError as exc:
        return _api_error(exc, "BrasilAPI")


@mcp.tool
async def brazil_company_lookup(cnpj: str) -> dict:
    """Look up a Brazilian company by CNPJ in the federal registry.

    Returns legal name, trade name, registration status, size, main
    activity (CNAE), share capital, address, contact data, and partners
    (QSA). Data from Receita Federal via BrasilAPI. Accepts formatted
    or unformatted numeric CNPJs.
    """
    clean = re.sub(r"[.\-/\s]", "", cnpj)
    if not re.fullmatch(r"\d{14}", clean):
        return {"error": "CNPJ must be 14 digits (the public registry API "
                         "does not yet resolve alphanumeric CNPJs)"}
    try:
        return await apis.brazil_company(clean)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            return {"error": f"CNPJ {clean} not found in the registry"}
        return _api_error(exc, "BrasilAPI")
    except httpx.HTTPError as exc:
        return _api_error(exc, "BrasilAPI")


# ---------------------------------------------------------------------------
# Colombia
# ---------------------------------------------------------------------------

@mcp.tool
async def colombia_official_trm() -> dict:
    """Get Colombia's official TRM (Tasa Representativa del Mercado), USD to COP.

    The TRM is the legally binding exchange rate certified by the financial
    regulator — used for taxes, customs, and contracts. Includes validity dates.
    """
    try:
        return await apis.colombia_trm()
    except (httpx.HTTPError, LookupError, ValueError) as exc:
        return _api_error(exc, "datos.gov.co")


# ---------------------------------------------------------------------------
# Costa Rica
# ---------------------------------------------------------------------------

@mcp.tool
async def costa_rica_company_lookup(cedula: str) -> dict:
    """Look up a Costa Rican taxpayer/company by cédula in the Hacienda registry.

    Accepts a cédula física (9 digits), jurídica (10 digits) or DIMEX.
    Returns legal name, tax regime, registered economic activities, and the
    tax-compliance situation — `delinquent` (moroso), `non_filer` (omiso)
    and registration `state` — which is valuable for KYC/AML and onboarding.
    Source: Ministerio de Hacienda (official, no key).
    """
    clean = re.sub(r"[.\-\s]", "", cedula)
    if not re.fullmatch(r"[0-9]{9,12}", clean):
        return {"error": "cédula must be 9-12 digits"}
    try:
        return await apis.costa_rica_company(clean)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code in (404, 500):
            return {"error": f"no taxpayer found for cédula {clean}"}
        return _api_error(exc, "Hacienda CR")
    except httpx.HTTPError as exc:
        return _api_error(exc, "Hacienda CR")


@mcp.tool
async def costa_rica_exchange_rate() -> dict:
    """Get Costa Rica's official USD and EUR exchange rates (colón, CRC).

    Buy/sell for USD and the EUR reference, as certified by Hacienda —
    used for invoicing and accounting in Costa Rica.
    """
    try:
        return {"currency": "CRC", **await apis.costa_rica_fx()}
    except httpx.HTTPError as exc:
        return _api_error(exc, "Hacienda CR")


# ---------------------------------------------------------------------------
# Regional FX
# ---------------------------------------------------------------------------

@mcp.tool
async def currency_convert(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount between any two currencies at the current rate.

    Handy for pricing, invoicing and reporting across LatAm — e.g. convert
    a Brazilian price to Chilean pesos. Uses live USD-based rates
    (open.er-api.com); covers all LatAm currencies plus USD/EUR and most
    world currencies. Currency codes are ISO 4217 (e.g. CLP, BRL, USD).
    """
    src = from_currency.strip().upper()
    dst = to_currency.strip().upper()
    try:
        data = await apis.usd_rates()
    except httpx.HTTPError as exc:
        return _api_error(exc, "open.er-api.com")
    rates = data["rates"]
    missing = [c for c in (src, dst) if c not in rates]
    if missing:
        return {"error": f"unknown currency code(s): {', '.join(missing)}"}
    # rates are units per 1 USD; go via USD
    result = amount / rates[src] * rates[dst]
    return {
        "amount": amount, "from": src, "to": dst,
        "converted": round(result, 4),
        "rate": round(rates[dst] / rates[src], 6),
        "last_update": data["last_update"],
    }


@mcp.tool
async def latam_exchange_rates(currencies: list[str] | None = None) -> dict:
    """Get current USD exchange rates for all Latin American currencies at once.

    Covers ARS, BOB, BRL, CLP, COP, CRC, CUP, DOP, GTQ, HNL, MXN, NIO,
    PAB, PEN, PYG, UYU, VES. Optionally filter with `currencies`.
    Rates are units of local currency per 1 USD, updated daily.
    """
    try:
        data = await apis.latam_fx()
    except httpx.HTTPError as exc:
        return _api_error(exc, "open.er-api.com")
    if currencies:
        wanted = {c.strip().upper() for c in currencies}
        data["rates"] = {k: v for k, v in data["rates"].items() if k in wanted}
        missing = wanted - data["rates"].keys()
        if missing:
            data["not_found"] = sorted(missing)
    return data


# ---------------------------------------------------------------------------
# Holidays & working days
# ---------------------------------------------------------------------------

def _check_country(country: str) -> str | dict:
    code = country.strip().upper()
    if code not in apis.LATAM_COUNTRIES:
        return {"error": f"'{country}' is not a supported Latin American country code",
                "supported": apis.LATAM_COUNTRIES}
    return code


@mcp.tool
async def public_holidays(country: str, year: int) -> dict:
    """Get official public holidays for a Latin American country and year.

    `country` is an ISO 3166-1 alpha-2 code (CL, AR, MX, BR, CO, PE, UY, ...).
    Returns each holiday with date, local name, English name, and whether
    it is nationwide. Useful for scheduling, SLAs, logistics, and payroll.
    """
    code = _check_country(country)
    if isinstance(code, dict):
        return code
    if err := _check_year(year):
        return err
    try:
        items = await apis.holidays(code, year)
    except httpx.HTTPError as exc:
        return _api_error(exc, "Nager.Date")
    return {"country": apis.LATAM_COUNTRIES[code], "year": year,
            "count": len(items), "holidays": items}


@mcp.tool
async def next_holidays(country: str) -> dict:
    """Get the upcoming public holidays for a Latin American country from today."""
    code = _check_country(country)
    if isinstance(code, dict):
        return code
    try:
        items = await apis.next_holidays(code)
    except httpx.HTTPError as exc:
        return _api_error(exc, "Nager.Date")
    return {"country": apis.LATAM_COUNTRIES[code], "upcoming": items}


@mcp.tool
async def long_weekends(country: str, year: int) -> dict:
    """Get long weekends for a Latin American country and year.

    Returns each long weekend with start/end dates, day count, and any
    bridge day needed — useful for travel, staffing, and demand planning.
    """
    code = _check_country(country)
    if isinstance(code, dict):
        return code
    if err := _check_year(year):
        return err
    try:
        items = await apis.long_weekends(code, year)
    except httpx.HTTPError as exc:
        return _api_error(exc, "Nager.Date")
    return {"country": apis.LATAM_COUNTRIES[code], "year": year,
            "long_weekends": items}


@mcp.tool
async def business_days(country: str, start_date: str, end_date: str) -> dict:
    """Count business days between two dates in a Latin American country.

    Excludes weekends and that country's nationwide public holidays.
    Dates are ISO format (YYYY-MM-DD); the range is inclusive on both ends.
    Returns the count plus the nationwide holidays that fell on a weekday
    inside the range (i.e. those that actually reduced the count) — useful
    for SLA, payroll, logistics and settlement-date math.
    """
    code = _check_country(country)
    if isinstance(code, dict):
        return code
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError as exc:
        return {"error": f"invalid date: {exc}"}
    if start > end:
        return {"error": "start_date must be on or before end_date"}
    if (end - start).days > 1500:
        return {"error": "range too large (max ~4 years)"}
    if err := (_check_year(start.year) or _check_year(end.year)):
        return err

    holiday_map: dict[str, str] = {}
    for year in range(start.year, end.year + 1):
        try:
            items = await apis.holidays(code, year)
        except httpx.HTTPError as exc:
            return _api_error(exc, "Nager.Date")
        for h in items:
            if h["nationwide"]:
                holiday_map[h["date"]] = h["local_name"]

    count, skipped = 0, []
    for ordinal in range(start.toordinal(), end.toordinal() + 1):
        day = date.fromordinal(ordinal)
        if day.weekday() >= 5:
            continue
        iso = day.isoformat()
        if iso in holiday_map:
            skipped.append({"date": iso, "holiday": holiday_map[iso]})
        else:
            count += 1

    return {"country": apis.LATAM_COUNTRIES[code], "start": start_date, "end": end_date,
            "business_days": count, "holidays_in_range": skipped}


def main() -> None:
    """Console entrypoint (`latam-data-mcp`).

    Dual-mode: hosting platforms (Render, Smithery, Fly, ...) set $PORT, which
    switches us to Streamable HTTP on all interfaces. With no $PORT we default
    to stdio, so local clients (Claude Desktop, Cursor, Claude Code) can spawn it.
    """
    import os

    port = os.environ.get("PORT")
    if port:
        mcp.run(transport="http", host="0.0.0.0", port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
