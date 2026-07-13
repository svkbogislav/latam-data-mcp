"""Data-source clients: free public APIs, no keys required.

Every function returns plain dicts/lists ready to serialize. Network
errors bubble up as httpx exceptions; the tool layer converts them
into structured error responses.
"""

from __future__ import annotations

from typing import Any

import httpx

USER_AGENT = "latam-data-mcp/0.2"

LATAM_COUNTRIES = {
    "AR": "Argentina", "BO": "Bolivia", "BR": "Brazil", "CL": "Chile",
    "CO": "Colombia", "CR": "Costa Rica", "CU": "Cuba", "DO": "Dominican Republic",
    "EC": "Ecuador", "SV": "El Salvador", "GT": "Guatemala", "HN": "Honduras",
    "MX": "Mexico", "NI": "Nicaragua", "PA": "Panama", "PY": "Paraguay",
    "PE": "Peru", "PR": "Puerto Rico", "UY": "Uruguay", "VE": "Venezuela",
}

LATAM_CURRENCIES = {
    "ARS": "Argentine peso", "BOB": "Bolivian boliviano", "BRL": "Brazilian real",
    "CLP": "Chilean peso", "COP": "Colombian peso", "CRC": "Costa Rican colón",
    "CUP": "Cuban peso", "DOP": "Dominican peso", "GTQ": "Guatemalan quetzal",
    "HNL": "Honduran lempira", "MXN": "Mexican peso", "NIO": "Nicaraguan córdoba",
    "PAB": "Panamanian balboa", "PEN": "Peruvian sol", "PYG": "Paraguayan guaraní",
    "USD": "US dollar (EC/SV/PA official)", "UYU": "Uruguayan peso", "VES": "Venezuelan bolívar",
}


class EmptyResponseError(httpx.HTTPError):
    """Upstream returned a 2xx with no body — treated as a transient failure.

    Subclasses httpx.HTTPError so the tool layer's existing `except httpx.HTTPError`
    catches it and returns a structured error instead of leaking a TypeError.
    """

    def __init__(self, url: str) -> None:
        super().__init__(f"empty response body from {url}")


async def _get_json(url: str, user_agent: str = USER_AGENT) -> Any:
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": user_agent},
                                 follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        if resp.status_code == 204 or not resp.content:
            raise EmptyResponseError(url)
        return resp.json()


# --- Chile ------------------------------------------------------------------

async def chile_indicators() -> list[dict]:
    data = await _get_json("https://api.gael.cloud/general/public/monedas")
    out = []
    for row in data:
        code = row.get("Codigo", "").strip().upper()
        raw = row.get("Valor", "").replace(".", "").replace(",", ".")
        try:
            out.append({"code": code, "name": row.get("Nombre", "").strip(),
                        "value_clp": float(raw)})
        except ValueError:
            continue
    return out


# --- Argentina ----------------------------------------------------------------

async def argentina_rates() -> dict:
    data = await _get_json("https://api.bluelytics.com.ar/v2/latest")

    def rate(key: str) -> dict | None:
        row = data.get(key)
        if not row:
            return None
        return {"buy": row["value_buy"], "sell": row["value_sell"], "avg": row["value_avg"]}

    return {
        "usd_official": rate("oficial"), "usd_blue": rate("blue"),
        "eur_official": rate("oficial_euro"), "eur_blue": rate("blue_euro"),
        "last_update": data.get("last_update"),
    }


# --- Brazil -------------------------------------------------------------------

async def brazil_rates() -> list[dict]:
    data = await _get_json("https://brasilapi.com.br/api/taxas/v1")
    return [{"name": r["nome"], "annual_pct": r["valor"]} for r in data]


async def brazil_company(cnpj: str) -> dict:
    data = await _get_json(f"https://brasilapi.com.br/api/cnpj/v1/{cnpj}")
    partners = [
        {"name": p.get("nome_socio"), "role": p.get("qualificacao_socio"),
         "joined": p.get("data_entrada_sociedade")}
        for p in data.get("qsa", [])
    ]
    return {
        "cnpj": data.get("cnpj"),
        "legal_name": data.get("razao_social"),
        "trade_name": data.get("nome_fantasia") or None,
        "status": data.get("descricao_situacao_cadastral"),
        "opened": data.get("data_inicio_atividade"),
        "size": data.get("porte"),
        "legal_nature": data.get("natureza_juridica"),
        "main_activity": data.get("cnae_fiscal_descricao"),
        "share_capital_brl": data.get("capital_social"),
        "address": {
            "street": data.get("logradouro"), "number": data.get("numero"),
            "district": data.get("bairro"), "city": data.get("municipio"),
            "state": data.get("uf"), "zip": data.get("cep"),
        },
        "phone": data.get("ddd_telefone_1") or None,
        "email": data.get("email") or None,
        "partners": partners,
    }


# --- Colombia -------------------------------------------------------------------

async def colombia_trm() -> dict:
    data = await _get_json(
        "https://www.datos.gov.co/resource/32sa-8pi3.json?$limit=1&$order=vigenciadesde%20DESC")
    row = data[0]
    return {
        "usd_cop": float(row["valor"]),
        "valid_from": row.get("vigenciadesde"),
        "valid_to": row.get("vigenciahasta"),
        "source": "Superintendencia Financiera de Colombia (official TRM)",
    }


# --- Costa Rica -----------------------------------------------------------------

# Hacienda's WAF rejects browser-like and custom User-Agents (403) but allows curl.
_CR_UA = "curl/8.4.0"


async def costa_rica_company(cedula: str) -> dict:
    data = await _get_json(f"https://api.hacienda.go.cr/fe/ae?identificacion={cedula}", _CR_UA)
    situacion = data.get("situacion") or {}
    return {
        "id": cedula,
        "name": data.get("nombre"),
        "regime": (data.get("regimen") or {}).get("descripcion"),
        "status": {
            "delinquent": situacion.get("moroso"),
            "non_filer": situacion.get("omiso"),
            "state": situacion.get("estado"),
            "tax_office": situacion.get("administracionTributaria"),
        },
        "activities": [
            {"code": a.get("codigo"), "description": a.get("descripcion"),
             "active": a.get("estado") == "A"}
            for a in (data.get("actividades") or [])
        ],
    }


async def costa_rica_fx() -> dict:
    data = await _get_json("https://api.hacienda.go.cr/indicadores/tc", _CR_UA)
    dolar = data.get("dolar") or {}
    euro = data.get("euro") or {}
    return {
        "usd_crc": {"buy": (dolar.get("compra") or {}).get("valor"),
                    "sell": (dolar.get("venta") or {}).get("valor"),
                    "date": (dolar.get("venta") or {}).get("fecha")},
        "eur_crc": {"value": euro.get("colones"), "date": euro.get("fecha")},
    }


# --- Regional FX -----------------------------------------------------------------

async def usd_rates() -> dict:
    data = await _get_json("https://open.er-api.com/v6/latest/USD")
    return {"rates": data.get("rates", {}), "last_update": data.get("time_last_update_utc")}


async def latam_fx() -> dict:
    data = await _get_json("https://open.er-api.com/v6/latest/USD")
    rates = data.get("rates", {})
    return {
        "base": "USD",
        "rates": {code: {"name": name, "per_usd": rates[code]}
                  for code, name in sorted(LATAM_CURRENCIES.items()) if code in rates},
        "last_update": data.get("time_last_update_utc"),
    }


# --- Holidays --------------------------------------------------------------------

async def holidays(country: str, year: int) -> list[dict]:
    data = await _get_json(f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country}")
    return [{"date": h["date"], "local_name": h["localName"], "name": h["name"],
             "nationwide": h.get("global", True)} for h in data]


async def next_holidays(country: str) -> list[dict]:
    data = await _get_json(f"https://date.nager.at/api/v3/NextPublicHolidays/{country}")
    return [{"date": h["date"], "local_name": h["localName"], "name": h["name"]}
            for h in data]


async def long_weekends(country: str, year: int) -> list[dict]:
    data = await _get_json(f"https://date.nager.at/api/v3/LongWeekend/{year}/{country}")
    return [{"start": w["startDate"], "end": w["endDate"], "days": w["dayCount"],
             "needs_bridge_day": w["needBridgeDay"], "bridge_days": w.get("bridgeDays", [])}
            for w in data]
